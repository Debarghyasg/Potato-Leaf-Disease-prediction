const express        = require('express');
const path           = require('path');
const bcrypt         = require('bcrypt');
const session        = require('express-session');
const { Client }     = require('pg');
const multer         = require('multer');
const axios          = require('axios');
const FormData       = require('form-data');
const nodemailer     = require('nodemailer');
const cron           = require('node-cron');
const fs             = require('fs');
const passport       = require('passport');
const LocalStrategy  = require('passport-local').Strategy;
const GoogleStrategy = require('passport-google-oauth20').Strategy;
require('dotenv').config();

const app         = express();
const port        = 3000;
const SALT_ROUNDS = 10;
const FLASK_URL   = process.env.FLASK_URL || 'http://localhost:5000';
const UPLOADS_DIR = path.join(__dirname, 'public', 'uploads');

const TRIAL_SCAN_LIMIT = 3;


// ── Database ──────────────────────────────────────────────────────────────────
const client = new Client({
    user:     'postgres',
    host:     'localhost',
    database: 'Potato-Disease',
    password: '1221',
    port:     5432,
});

client.connect()
    .then(async () => {
        console.log('✅ Connected to PostgreSQL');
        await client.query(`
            CREATE TABLE IF NOT EXISTS trial_scans (
                phone       VARCHAR(15) PRIMARY KEY,
                name        VARCHAR(100) NOT NULL,
                scans_used  INT          NOT NULL DEFAULT 0,
                first_seen  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_seen   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        `);
        console.log('✅ trial_scans table ready');
    })
    .catch(err => { console.error('❌ DB connection failed:', err.message); process.exit(1); });


// ── Nodemailer ────────────────────────────────────────────────────────────────
const transporter = nodemailer.createTransport({
    service: 'gmail',
    auth: {
        user: process.env.EMAIL_USER,
        pass: process.env.EMAIL_PASS,
    },
});

const sendWelcomeEmail = async (userEmail, userName) => {
    try {
        const mailOptions = {
            from:    `"PotatoScan Support" <${process.env.EMAIL_USER}>`,
            to:      userEmail,
            subject: 'Welcome to PotatoScan! 🌿',
            html: `
                <div style="font-family:sans-serif;max-width:600px;border:1px solid #eee;padding:20px;border-radius:10px;">
                    <h2 style="color:#4a8c3f;">Welcome to the family, ${userName}!</h2>
                    <p>Thanks for joining <b>PotatoScan</b>. We're excited to help you keep your crops healthy using AI.</p>
                    <p style="color:#3f9949; font-family:sans-serif; font-size:18px; font-weight:bold; margin:20px 0;">
                    AI is useful for those who need it the most, This one for the Farmers.🌿
                    </p>
                    <p>You can now upload leaf images and get instant diagnoses for Early Blight, Late Blight, or confirm your plants are Healthy.</p>
                    <br>
                    <a href="https://github.com/Debarghyasg/Potato-Leaf-Disease-prediction"
                       style="background:#4a8c3f;color:white;padding:12px 25px;text-decoration:none;border-radius:5px;display:inline-block;">
                       Start Your First Scan
                    </a>
                    
                    <p style="margin-top:30px;font-size:12px;color:#888;border-top:1px solid #eee;padding-top:10px;">
                        Powered by Deep Learning
                    </p>
                </div>
            `,
        };
        await transporter.sendMail(mailOptions);
        console.log('📧 Welcome email sent to:', userEmail);
    } catch (error) {
        console.error('❌ Email failed:', error.message);
    }
};


// ── Multer ────────────────────────────────────────────────────────────────────
if (!fs.existsSync(UPLOADS_DIR)) {
    fs.mkdirSync(UPLOADS_DIR, { recursive: true });
}

const storage = multer.diskStorage({
    destination: (req, file, cb) => cb(null, UPLOADS_DIR),
    filename:    (req, file, cb) => {
        const uniqueName = Date.now() + '_' + file.originalname.replace(/\s+/g, '_');
        cb(null, uniqueName);
    },
});

const upload = multer({
    storage,
    limits: { fileSize: 10 * 1024 * 1024 },
    fileFilter: (req, file, cb) => {
        const allowed = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
        allowed.includes(file.mimetype)
            ? cb(null, true)
            : cb(new Error('Only JPG, PNG, and WEBP allowed.'));
    },
});


// ── Middleware ────────────────────────────────────────────────────────────────
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'public')));

app.use(session({
    secret:            process.env.SESSION_SECRET || 'your_secret_key',
    resave:            false,
    saveUninitialized: false,
    rolling:           true,
    cookie: {
        maxAge:   30 * 60 * 1000,
        httpOnly: true,
        secure:   false,
    },
}));

app.use(passport.initialize());
app.use(passport.session());


// ── View Engine ───────────────────────────────────────────────────────────────
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));


// ── Auth Middleware ───────────────────────────────────────────────────────────
const isAuth = (req, res, next) => {
    if (req.session.user) return next();
    res.redirect('/');
};

// ── Trial Valid Middleware ────────────────────────────────────────────────────
const isTrialValid = async (req, res, next) => {
    if (!req.session.user?.isTrial) return next();
    try {
        const row = await client.query(
            'SELECT scans_used FROM trial_scans WHERE phone = $1',
            [req.session.user.phone]
        );
        const scansUsed = row.rows.length > 0 ? row.rows[0].scans_used : 0;
        if (scansUsed >= TRIAL_SCAN_LIMIT) {
            req.session.destroy(() => {});
            return res.redirect('/?trial=exhausted');
        }
        next();
    } catch (err) {
        console.error('Trial validation error:', err.message);
        res.redirect('/');
    }
};


// ── Passport: Local Strategy ──────────────────────────────────────────────────
passport.use(new LocalStrategy(
    { usernameField: 'email', passwordField: 'password' },
    async (email, password, done) => {
        try {
            const result = await client.query(
                'SELECT * FROM users WHERE email = $1', [email]
            );
            if (result.rows.length === 0)
                return done(null, false, { message: 'Invalid email or password.' });

            const user = result.rows[0];

            if (user.password === 'GOOGLE_OAUTH')
                return done(null, false, { message: 'Please sign in with Google for this account.' });

            const isMatch = await bcrypt.compare(password, user.password);
            if (!isMatch)
                return done(null, false, { message: 'Invalid email or password.' });

            return done(null, user);
        } catch (err) {
            return done(err);
        }
    }
));


// ── Passport: Google OAuth Strategy ──────────────────────────────────────────
passport.use(new GoogleStrategy(
    {
        clientID:     process.env.GOOGLE_CLIENT_ID,
        clientSecret: process.env.GOOGLE_CLIENT_SECRET,
        callbackURL:  '/auth/google/callback',
    },
    async (accessToken, refreshToken, profile, done) => {
        try {
            const email     = profile.emails[0].value;
            const firstname = profile.name.givenName;
            const lastname  = profile.name.familyName;

            const existing = await client.query(
                'SELECT * FROM users WHERE email = $1', [email]
            );

            if (existing.rows.length > 0) {
                const user = existing.rows[0];
                user.isNewGoogleUser = false;
                return done(null, user);
            }

            const newUser = await client.query(
                `INSERT INTO users (firstname, lastname, email, password, phone, location, terms_accepted)
                 VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING *`,
                [firstname, lastname, email, 'GOOGLE_OAUTH', '', '', true]
            );

            const user = newUser.rows[0];
            user.isNewGoogleUser = true;
            return done(null, user);

        } catch (err) {
            return done(err);
        }
    }
));

passport.serializeUser((user, done) => done(null, user.id));

passport.deserializeUser(async (id, done) => {
    try {
        const result = await client.query('SELECT * FROM users WHERE id = $1', [id]);
        done(null, result.rows[0]);
    } catch (err) {
        done(err);
    }
});


// ── ROUTES ────────────────────────────────────────────────────────────────────

// GET / — Login page
app.get('/', (req, res) => {
    if (req.session.user) return res.redirect('/home');
    res.render('Login_multilang.ejs');
});

// GET /home
app.get('/home', isAuth, isTrialValid, async (req, res) => {
    try {
        if (req.session.user.isTrial) {
            const trialRow = await client.query(
                'SELECT scans_used FROM trial_scans WHERE phone = $1',
                [req.session.user.phone]
            );
            const scansUsed = trialRow.rows.length > 0 ? trialRow.rows[0].scans_used : 0;
            const user = {
                firstname: req.session.user.name,
                lastname:  '',
                email:     null,
                isTrial:   true,
                scansUsed,
                scansLeft: TRIAL_SCAN_LIMIT - scansUsed,
            };
            return res.render('index_multilang.ejs', { user });
        }

        const result = await client.query(
            'SELECT * FROM users WHERE id = $1', [req.session.user.id]
        );
        res.render('index_multilang.ejs', { user: result.rows[0] });
    } catch (err) {
        console.error('Home route error:', err.message);
        res.redirect('/');
    }
});

// GET /signup
app.get('/signup', (req, res) => {
    if (req.session.user) return res.redirect('/home');
    res.render('signup_multilang.ejs');
});

// POST /signup
app.post('/signup', async (req, res) => {
    const { firstname, lastname, email, password, phone, location, terms_accepted } = req.body;

    if (!firstname || !lastname || !email || !password || !phone || !location)
        return res.status(400).send('All fields are required.');

    if (password.length < 8)
        return res.status(400).send('Password must be at least 8 characters.');

    try {
        const existing = await client.query(
            'SELECT id FROM users WHERE email = $1', [email]
        );
        if (existing.rows.length > 0)
            return res.status(409).send('An account with this email already exists.');

        const hashedPassword = await bcrypt.hash(password, SALT_ROUNDS);

        await client.query(
            `INSERT INTO users (firstname, lastname, email, password, phone, location, terms_accepted)
             VALUES ($1, $2, $3, $4, $5, $6, $7)`,
            [firstname, lastname, email, hashedPassword, phone, location, terms_accepted ? true : false]
        );

        sendWelcomeEmail(email, firstname);

        req.session.save(err => {
            if (err) {
                console.error('Session save error:', err);
                return res.status(500).send('Error saving session.');
            }
            res.redirect('/');
        });

    } catch (err) {
        console.error('Signup error:', err.message);
        res.status(500).send('Server error.');
    }
});

// POST / — Login
app.post('/', async (req, res) => {
    const { email, password } = req.body;

    if (!email || !password)
        return res.status(400).send('Email and password are required.');

    try {
        const result = await client.query(
            'SELECT * FROM users WHERE email = $1', [email]
        );

        if (result.rows.length === 0)
            return res.status(401).send('Invalid email or password.');

        const user = result.rows[0];

        if (user.password === 'GOOGLE_OAUTH')
            return res.status(401).send('Please sign in with Google for this account.');

        const isMatch = await bcrypt.compare(password, user.password);
        if (!isMatch)
            return res.status(401).send('Invalid email or password.');

        req.session.regenerate(err => {
            if (err) return res.status(500).send('Session error.');
            req.session.user = { id: user.id, name: user.firstname };
            res.redirect('/home');
        });

    } catch (err) {
        console.error('Login error:', err.message);
        res.status(500).send('Server error.');
    }
});

// GET /auth/google
app.get('/auth/google',
    passport.authenticate('google', { scope: ['profile', 'email'] })
);

// GET /auth/google/callback
app.get('/auth/google/callback',
    passport.authenticate('google', { failureRedirect: '/' }),
    (req, res) => {
        const user = req.user;
        req.session.user = { id: user.id, name: user.firstname };

        if (user.isNewGoogleUser) {
            sendWelcomeEmail(user.email, user.firstname);
            console.log('🆕 New Google user — welcome email queued for:', user.email);
        }

        res.redirect('/home');
    }
);


// ── POST /trial ───────────────────────────────────────────────────────────────
app.post('/trial', async (req, res) => {
    const trialname  = (req.body.trialname  || '').trim();
    const trialphone = (req.body.trialphone || '').replace(/\s/g, '');

    console.log('📋 Trial POST received:', { trialname, trialphone });

    if (!trialname || !trialphone)
        return res.status(400).send('Name and phone are required.');

    if (!/^\d{10}$/.test(trialphone)) {
        console.log('❌ Phone validation failed for:', trialphone);
        return res.status(400).send('Enter a valid 10-digit phone number.');
    }

    try {
        const existing = await client.query(
            'SELECT scans_used FROM trial_scans WHERE phone = $1',
            [trialphone]
        );
        console.log('🔍 DB lookup result:', existing.rows);

        if (existing.rows.length > 0) {
            const scansUsed = existing.rows[0].scans_used;

            if (scansUsed >= TRIAL_SCAN_LIMIT) {
                console.log('🚫 Trial limit reached for:', trialphone);
                return res.redirect('/?trial=exhausted');
            }

            // Returning trial user — update name and last_seen
            await client.query(
                `UPDATE trial_scans
                 SET name = $1, last_seen = CURRENT_TIMESTAMP
                 WHERE phone = $2`,
                [trialname, trialphone]
            );
            console.log('✅ Updated existing trial user:', trialphone);

        } else {
            // First time — insert with 0 scans
            await client.query(
                `INSERT INTO trial_scans (phone, name, scans_used)
                 VALUES ($1, $2, 0)`,
                [trialphone, trialname]
            );
            console.log('✅ Inserted new trial user:', trialphone);
        }

        req.session.regenerate(err => {
            if (err) return res.status(500).send('Session error.');
            req.session.user = {
                id:      null,
                name:    trialname,
                phone:   trialphone,
                isTrial: true,
            };
            res.redirect('/home');
        });

    } catch (err) {
        console.error('❌ Trial DB error:', err.message);
        res.status(500).send('Server error.');
    }
});


// GET /logout
app.get('/logout', (req, res) => {
    req.session.destroy(err => {
        if (err) console.error('Logout error:', err);
        res.redirect('/');
    });
});

// GET /result
app.get('/result', (req, res) => {
    res.render('result.ejs', { result: null, error: null, imageUrl: null });
});


// ── POST /analyze ─────────────────────────────────────────────────────────────
app.post('/analyze', isAuth, isTrialValid, upload.single('leafImage'), async (req, res) => {
    if (!req.file) {
        return res.render('result.ejs', {
            result: null,
            error: 'No image received.',
            imageUrl: null,
        });
    }

    const savedFilePath = req.file.path;
    const imageUrl      = '/uploads/' + req.file.filename;

    // ── Trial scan gate ───────────────────────────────────────────────────────
    if (req.session.user.isTrial) {
        const phone = req.session.user.phone;
        try {
            const row = await client.query(
                'SELECT scans_used FROM trial_scans WHERE phone = $1',
                [phone]
            );
            const scansUsed = row.rows.length > 0 ? row.rows[0].scans_used : 0;

            if (scansUsed >= TRIAL_SCAN_LIMIT) {
                fs.unlink(savedFilePath, () => {});
                req.session.destroy(() => {});
                return res.redirect('/?trial=exhausted');
            }

            // Increment BEFORE calling Flask
            await client.query(
                `UPDATE trial_scans
                 SET scans_used = scans_used + 1,
                     last_seen  = CURRENT_TIMESTAMP
                 WHERE phone = $1`,
                [phone]
            );
            console.log(`📸 Trial scan ${scansUsed + 1}/${TRIAL_SCAN_LIMIT} used for:`, phone);

            req.session.user.scansUsed = scansUsed + 1;

        } catch (dbErr) {
            console.error('Trial scan DB error:', dbErr.message);
            fs.unlink(savedFilePath, () => {});
            return res.render('result.ejs', {
                result: null, imageUrl: null,
                error: 'Server error while checking trial quota.',
            });
        }
    }
    // ─────────────────────────────────────────────────────────────────────────

    try {
        const form = new FormData();
        form.append('file', fs.createReadStream(savedFilePath), {
            filename:    req.file.originalname,
            contentType: req.file.mimetype,
        });

        const response = await axios.post(`${FLASK_URL}/predict`, form, {
            headers: form.getHeaders(),
            timeout: 200000,
        });

        res.render('result.ejs', {
            result:   response.data,
            error:    null,
            imageUrl,
        });

    } catch (err) {
        const errorMsg = err.code === 'ECONNREFUSED'
            ? 'ML server (Flask) is offline. Please try again later.'
            : `Analysis error: ${err.message}`;

        res.render('result.ejs', { result: null, error: errorMsg, imageUrl });
    }
});


// ── Error Handler ─────────────────────────────────────────────────────────────
app.use((err, req, res, next) => {
    if (err instanceof multer.MulterError || err.message?.includes('Only')) {
        return res.render('result.ejs', { result: null, error: err.message, imageUrl: null });
    }
    console.error('Unhandled error:', err.message);
    next(err);
});


// ── Start Server ──────────────────────────────────────────────────────────────
app.listen(port, () => {
    console.log(`🚀 Server running on http://localhost:${port}`);
    console.log(`🧠 Flask backend: ${FLASK_URL}`);
});