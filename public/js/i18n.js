// ═══════════════════════════════════════════════════════════════
//  PotatoScan — i18n Translation Engine
//  Supports: English (en), Hindi (hi), Bengali (bn)
//  Usage: include this script, then call i18n.init()
// ═══════════════════════════════════════════════════════════════

const i18n = (() => {

  // ── Translation Dictionary ──────────────────────────────────
  const translations = {

    // ── LOGIN PAGE ───────────────────────────────────────────
    'login.eyebrow':           { en: 'Sign In',          hi: 'साइन इन',       bn: 'সাইন ইন' },
    'login.title1':            { en: 'Hello,',           hi: 'नमस्ते,',        bn: 'নমস্কার,' },
    'login.title2':            { en: 'Again',            hi: 'फिर से',         bn: 'আবার' },
    'login.sub':               { en: "Don't have an account?", hi: 'खाता नहीं है?', bn: 'অ্যাকাউন্ট নেই?' },
    'login.sub.link':          { en: 'Create one free →', hi: 'मुफ़्त बनाएं →',  bn: 'বিনামূল্যে তৈরি করুন →' },
    'login.email.label':       { en: 'Email Address',    hi: 'ईमेल पता',       bn: 'ইমেইল ঠিকানা' },
    'login.email.placeholder': { en: 'you@example.com',  hi: 'आप@example.com', bn: 'আপনি@example.com' },
    'login.pass.label':        { en: 'Password',         hi: 'पासवर्ड',         bn: 'পাসওয়ার্ড' },
    'login.pass.placeholder':  { en: 'Enter your password', hi: 'पासवर्ड डालें', bn: 'পাসওয়ার্ড লিখুন' },
    'login.forgot':            { en: 'Forgot password?', hi: 'पासवर्ड भूल गए?', bn: 'পাসওয়ার্ড ভুলে গেছেন?' },
    'login.remember':          { en: 'Remember me for 30 days', hi: '30 दिनों तक याद रखें', bn: '৩০ দিন মনে রাখুন' },
    'login.btn':               { en: 'Sign In →',        hi: 'साइन इन करें →',  bn: 'সাইন ইন করুন →' },
    'login.btn.loading':       { en: 'Signing In…',      hi: 'साइन हो रहा है…', bn: 'সাইন হচ্ছে…' },
    'login.or':                { en: 'or continue with', hi: 'या जारी रखें',    bn: 'বা চালিয়ে যান' },
    'login.google':            { en: 'Continue with Google', hi: 'Google से जारी रखें', bn: 'Google দিয়ে চালিয়ে যান' },
    'login.or.trial':          { en: 'or try for free',  hi: 'या मुफ़्त में आज़माएं', bn: 'বা বিনামূল্যে চেষ্টা করুন' },
    'login.trial.btn':         { en: 'Try Without Account', hi: 'बिना खाते के आज़माएं', bn: 'অ্যাকাউন্ট ছাড়া চেষ্টা করুন' },
    'login.trial.hint':        { en: 'No sign-up · Just name & phone · 3 free scans', hi: 'कोई रजिस्ट्रेशन नहीं · सिर्फ नाम और फ़ोन · 3 मुफ़्त स्कैन', bn: 'নিবন্ধন নেই · শুধু নাম ও ফোন · ৩টি বিনামূল্যে স্ক্যান' },
    'login.err.fix':           { en: 'Please fix the errors above.', hi: 'कृपया ऊपर की त्रुटियां ठीक करें।', bn: 'দয়া করে উপরের ত্রুটিগুলো ঠিক করুন।' },
    'login.err.invalid':       { en: 'Invalid email or password.', hi: 'ईमेल या पासवर्ड गलत है।', bn: 'ইমেইল বা পাসওয়ার্ড ভুল।' },
    'login.err.network':       { en: 'Network error. Please try again.', hi: 'नेटवर्क त्रुटि। फिर से प्रयास करें।', bn: 'নেটওয়ার্ক ত্রুটি। আবার চেষ্টা করুন।' },
    'login.err.email':         { en: 'Please enter a valid email address', hi: 'कृपया वैध ईमेल दर्ज करें', bn: 'সঠিক ইমেইল ঠিকানা লিখুন' },
    'login.err.pass':          { en: 'Password must be at least 6 characters', hi: 'पासवर्ड कम से कम 6 अक्षर का होना चाहिए', bn: 'পাসওয়ার্ড কমপক্ষে ৬ অক্ষরের হতে হবে' },
    'login.success.title1':    { en: "You're", hi: 'आप',             bn: 'আপনি' },
    'login.success.title2':    { en: 'In!',    hi: 'अंदर हैं!',       bn: 'ভেতরে!' },
    'login.success.desc':      { en: 'Welcome back. Redirecting you to your dashboard.', hi: 'वापसी पर स्वागत है। डैशबोर्ड पर जा रहे हैं।', bn: 'স্বাগতম। ড্যাশবোর্ডে যাচ্ছি।' },
    'login.success.btn':       { en: 'Go to Dashboard', hi: 'डैशबोर्ड पर जाएं', bn: 'ড্যাশবোর্ডে যান' },
    'login.panel.desc':        { en: 'Sign in to access your dashboard, view past diagnoses, and protect your potato crops with AI precision.', hi: 'अपने डैशबोर्ड तक पहुंचने के लिए साइन इन करें।', bn: 'আপনার ড্যাশবোর্ড অ্যাক্সেস করতে সাইন ইন করুন।' },
    'login.stat.accuracy':     { en: 'Accuracy',   hi: 'सटीकता',      bn: 'নির্ভুলতা' },
    'login.stat.analysis':     { en: 'Analysis',   hi: 'विश्लेषण',    bn: 'বিশ্লেষণ' },
    'login.stat.scans':        { en: 'Scans Done', hi: 'स्कैन हुए',    bn: 'স্ক্যান হয়েছে' },

    // ── TRIAL MODAL ──────────────────────────────────────────
    'trial.badge':       { en: '⚡ Free Trial',   hi: '⚡ मुफ़्त ट्रायल', bn: '⚡ বিনামূল্যে ট্রায়াল' },
    'trial.title1':      { en: 'Try It',          hi: 'आज़माएं',         bn: 'চেষ্টা করুন' },
    'trial.title2':      { en: 'Free',            hi: 'मुफ़्त',           bn: 'বিনামূল্যে' },
    'trial.desc':        { en: 'No account needed. Just enter your name and phone number to get instant access.', hi: 'कोई खाता जरूरी नहीं। बस नाम और फ़ोन नंबर डालें।', bn: 'কোনো অ্যাকাউন্ট দরকার নেই। শুধু নাম ও ফোন নম্বর দিন।' },
    'trial.name.label':  { en: 'Your Name',       hi: 'आपका नाम',        bn: 'আপনার নাম' },
    'trial.name.ph':     { en: 'e.g. Arjun',      hi: 'जैसे अर्जुन',     bn: 'যেমন অর্জুন' },
    'trial.name.err':    { en: 'Please enter your name (min. 2 characters)', hi: 'कृपया अपना नाम डालें (कम से कम 2 अक्षर)', bn: 'আপনার নাম লিখুন (কমপক্ষে ২ অক্ষর)' },
    'trial.phone.label': { en: 'Phone Number',    hi: 'फ़ोन नंबर',         bn: 'ফোন নম্বর' },
    'trial.phone.ph':    { en: '98765 43210',     hi: '98765 43210',     bn: '৯৮৭৬৫ ৪৩২১০' },
    'trial.phone.err':   { en: 'Enter a valid 10-digit number', hi: '10 अंकों का वैध नंबर डालें', bn: 'সঠিক ১০ সংখ্যার নম্বর দিন' },
    'trial.btn':         { en: 'Start Free Trial →', hi: 'मुफ़्त ट्रायल शुरू करें →', bn: 'বিনামূল্যে ট্রায়াল শুরু করুন →' },
    'trial.btn.loading': { en: 'Starting…',       hi: 'शुरू हो रहा है…', bn: 'শুরু হচ্ছে…' },
    'trial.note':        { en: 'No password · No email · Scan up to 3 images', hi: 'कोई पासवर्ड नहीं · कोई ईमेल नहीं · 3 तक स्कैन', bn: 'পাসওয়ার্ড নেই · ইমেইল নেই · ৩টি পর্যন্ত স্ক্যান' },

    // ── SIGNUP PAGE ──────────────────────────────────────────
    'signup.eyebrow':         { en: 'New Account',      hi: 'नया खाता',         bn: 'নতুন অ্যাকাউন্ট' },
    'signup.title1':          { en: 'Create Your',      hi: 'अपनी',              bn: 'আপনার' },
    'signup.title2':          { en: 'Profile',          hi: 'प्रोफाइल बनाएं',   bn: 'প্রোফাইল তৈরি করুন' },
    'signup.sub':             { en: 'Already have an account?', hi: 'पहले से खाता है?', bn: 'ইতিমধ্যে অ্যাকাউন্ট আছে?' },
    'signup.sub.link':        { en: 'Sign in here',     hi: 'यहाँ साइन इन करें', bn: 'এখানে সাইন ইন করুন' },
    'signup.progress.label':  { en: 'Profile Completion', hi: 'प्रोफाइल पूर्णता', bn: 'প্রোফাইল সম্পূর্ণতা' },
    'signup.firstname.label': { en: 'First Name',       hi: 'पहला नाम',          bn: 'প্রথম নাম' },
    'signup.firstname.ph':    { en: 'e.g. Arjun',       hi: 'जैसे अर्जुन',       bn: 'যেমন অর্জুন' },
    'signup.firstname.err':   { en: 'Please enter your first name', hi: 'कृपया पहला नाम डालें', bn: 'আপনার প্রথম নাম লিখুন' },
    'signup.lastname.label':  { en: 'Last Name',        hi: 'अंतिम नाम',         bn: 'শেষ নাম' },
    'signup.lastname.ph':     { en: 'e.g. Sharma',      hi: 'जैसे शर्मा',        bn: 'যেমন শর্মা' },
    'signup.lastname.err':    { en: 'Please enter your last name', hi: 'कृपया अंतिम नाम डालें', bn: 'আপনার শেষ নাম লিখুন' },
    'signup.email.label':     { en: 'Email Address',    hi: 'ईमेल पता',           bn: 'ইমেইল ঠিকানা' },
    'signup.email.ph':        { en: 'you@example.com',  hi: 'आप@example.com',    bn: 'আপনি@example.com' },
    'signup.email.err':       { en: 'Please enter a valid email address', hi: 'कृपया वैध ईमेल दर्ज करें', bn: 'সঠিক ইমেইল ঠিকানা লিখুন' },
    'signup.pass.label':      { en: 'Password',         hi: 'पासवर्ड',             bn: 'পাসওয়ার্ড' },
    'signup.pass.ph':         { en: 'Min. 8 characters', hi: 'न्यूनतम 8 अक्षर',   bn: 'কমপক্ষে ৮ অক্ষর' },
    'signup.pass.err':        { en: 'Password must be at least 8 characters', hi: 'पासवर्ड कम से कम 8 अक्षर का होना चाहिए', bn: 'পাসওয়ার্ড কমপক্ষে ৮ অক্ষরের হতে হবে' },
    'signup.pass.weak':       { en: 'WEAK',             hi: 'कमज़ोर',              bn: 'দুর্বল' },
    'signup.pass.moderate':   { en: 'MODERATE',         hi: 'ठीक-ठाक',            bn: 'মাঝারি' },
    'signup.pass.strong':     { en: 'STRONG',           hi: 'मज़बूत',              bn: 'শক্তিশালী' },
    'signup.pass.vstrong':    { en: 'VERY STRONG',      hi: 'बहुत मज़बूत',         bn: 'অত্যন্ত শক্তিশালী' },
    'signup.phone.label':     { en: 'Phone Number',     hi: 'फ़ोन नंबर',            bn: 'ফোন নম্বর' },
    'signup.phone.ph':        { en: '98765 43210',      hi: '98765 43210',        bn: '৯৮৭৬৫ ৪৩২১০' },
    'signup.phone.err':       { en: 'Enter a valid 10-digit phone number', hi: '10 अंकों का वैध फ़ोन नंबर डालें', bn: 'সঠিক ১০ সংখ্যার ফোন নম্বর দিন' },
    'signup.location.label':  { en: 'Location / Region', hi: 'स्थान / क्षेत्र',  bn: 'অবস্থান / অঞ্চল' },
    'signup.location.ph':     { en: 'e.g. West Bengal, India', hi: 'जैसे पश्चिम बंगाल, भारत', bn: 'যেমন পশ্চিমবঙ্গ, ভারত' },
    'signup.location.err':    { en: 'Please enter your location', hi: 'कृपया अपना स्थान डालें', bn: 'আপনার অবস্থান লিখুন' },
    'signup.terms':           { en: 'I agree to the', hi: 'मैं इससे सहमत हूं', bn: 'আমি সম্মত' },
    'signup.terms.tos':       { en: 'Terms of Service', hi: 'सेवा की शर्तें',   bn: 'পরিষেবার শর্তাবলী' },
    'signup.terms.pp':        { en: 'Privacy Policy',   hi: 'गोपनीयता नीति',   bn: 'গোপনীয়তা নীতি' },
    'signup.terms.note':      { en: 'I understand that my crop data may be used to improve the AI model anonymously.', hi: 'मैं समझता हूं कि मेरा फसल डेटा AI मॉडल को बेहतर बनाने के लिए गुमनाम रूप से उपयोग किया जा सकता है।', bn: 'আমি বুঝি যে আমার ফসলের ডেটা AI মডেল উন্নত করতে বেনামে ব্যবহার হতে পারে।' },
    'signup.btn':             { en: 'Create My Account →', hi: 'मेरा खाता बनाएं →', bn: 'আমার অ্যাকাউন্ট তৈরি করুন →' },
    'signup.btn.loading':     { en: 'Creating Account…', hi: 'खाता बन रहा है…',   bn: 'অ্যাকাউন্ট তৈরি হচ্ছে…' },
    'signup.panel.tagline':   { en: 'AI-Powered Leaf Disease Detection', hi: 'AI-संचालित रोग पहचान', bn: 'AI-চালিত রোগ শনাক্তকরণ' },
    'signup.panel.headline1': { en: 'Join The',          hi: 'शामिल हों',         bn: 'যোগ দিন' },
    'signup.panel.headline2': { en: 'Future',            hi: 'भविष्य में',         bn: 'ভবিষ্যতে' },
    'signup.panel.desc':      { en: "Create your free account and start diagnosing potato leaf diseases with 97.4% accuracy.", hi: "अपना मुफ़्त खाता बनाएं और 97.4% सटीकता के साथ रोग की पहचान शुरू करें।", bn: "বিনামূল্যে অ্যাকাউন্ট তৈরি করুন এবং ৯৭.৪% নির্ভুলতায় রোগ শনাক্ত করা শুরু করুন।" },
    'signup.feat1':           { en: 'AI-powered disease analysis in <2 seconds', hi: 'AI रोग विश्लेषण 2 सेकंड में', bn: 'AI রোগ বিশ্লেষণ ২ সেকেন্ডের মধ্যে' },
    'signup.feat2':           { en: 'Detailed reports with confidence scores',  hi: 'विश्वास स्कोर के साथ विस्तृत रिपोर्ट', bn: 'আত্মবিশ্বাস স্কোর সহ বিস্তারিত রিপোর্ট' },
    'signup.feat3':           { en: 'Secure & private — your data stays yours', hi: 'सुरक्षित और निजी — आपका डेटा आपका', bn: 'নিরাপদ ও গোপন — আপনার ডেটা আপনার' },
    'signup.feat4':           { en: 'Available worldwide, any device',          hi: 'दुनियाभर में उपलब्ध, किसी भी डिवाइस पर', bn: 'বিশ্বজুড়ে উপলব্ধ, যেকোনো ডিভাইসে' },
    'signup.success.title1':  { en: 'Welcome',           hi: 'स्वागत',            bn: 'স্বাগতম' },
    'signup.success.title2':  { en: 'Aboard!',           hi: 'है!',               bn: 'আপনাকে!' },
    'signup.success.desc':    { en: "Your account has been created. You're ready to start scanning.", hi: 'आपका खाता बन गया है। स्कैन शुरू करें।', bn: 'আপনার অ্যাকাউন্ট তৈরি হয়েছে। স্ক্যান শুরু করুন।' },
    'signup.success.btn':     { en: 'Start Scanning →',  hi: 'स्कैन शुरू करें →', bn: 'স্ক্যান শুরু করুন →' },

    // ── HOME / INDEX PAGE ────────────────────────────────────
    'home.badge':             { en: 'AI-Powered Diagnosis', hi: 'AI-संचालित निदान', bn: 'AI-চালিত রোগ নির্ণয়' },
    'home.hero.title1':       { en: 'Potato',            hi: 'आलू',               bn: 'আলু' },
    'home.hero.title2':       { en: 'Leaf',              hi: 'पत्ती',              bn: 'পাতা' },
    'home.hero.title3':       { en: 'Disease Scanner',   hi: 'रोग स्कैनर',         bn: 'রোগ স্ক্যানার' },
    'home.hero.desc':         { en: 'Upload a photo of your potato leaf and our deep-learning model identifies diseases instantly — protecting your harvest before damage spreads.', hi: 'अपनी आलू की पत्ती की फोटो अपलोड करें और हमारा AI मॉडल तुरंत रोग पहचानेगा।', bn: 'আপনার আলু পাতার ছবি আপলোড করুন এবং আমাদের AI মডেল তাৎক্ষণিকভাবে রোগ শনাক্ত করবে।' },
    'home.stat.accuracy':     { en: 'Accuracy',          hi: 'सटीकता',             bn: 'নির্ভুলতা' },
    'home.stat.diseases':     { en: 'Diseases Detected', hi: 'रोग पहचाने',         bn: 'রোগ শনাক্ত' },
    'home.stat.time':         { en: 'Analysis Time',     hi: 'विश्लेषण समय',       bn: 'বিশ্লেষণ সময়' },
    'home.upload.title':      { en: '// UPLOAD LEAF IMAGE', hi: '// पत्ती की छवि अपलोड करें', bn: '// পাতার ছবি আপলোড করুন' },
    'home.drop.main':         { en: 'Drop leaf image here', hi: 'यहाँ पत्ती की छवि छोड़ें', bn: 'এখানে পাতার ছবি ফেলুন' },
    'home.drop.sub':          { en: 'or click to browse files', hi: 'या फाइलें ब्राउज़ करें', bn: 'বা ফাইল খুঁজুন' },
    'home.preview.ready':     { en: 'Ready to analyze',  hi: 'विश्लेषण के लिए तैयार', bn: 'বিশ্লেষণের জন্য প্রস্তুত' },
    'home.change.img':        { en: '✕ Change image',    hi: '✕ छवि बदलें',        bn: '✕ ছবি পরিবর্তন করুন' },
    'home.analyze.btn':       { en: '⬡ Analyze Leaf',    hi: '⬡ पत्ती विश्लेषण करें', bn: '⬡ পাতা বিশ্লেষণ করুন' },
    'home.loading.1':         { en: 'SCANNING LEAF…',    hi: 'पत्ती स्कैन हो रही है…', bn: 'পাতা স্ক্যান হচ্ছে…' },
    'home.loading.2':         { en: 'EXTRACTING FEATURES…', hi: 'विशेषताएं निकाली जा रही हैं…', bn: 'বৈশিষ্ট্য বের করা হচ্ছে…' },
    'home.loading.3':         { en: 'RUNNING MODEL…',    hi: 'मॉडल चल रहा है…',   bn: 'মডেল চলছে…' },
    'home.loading.4':         { en: 'CLASSIFYING…',      hi: 'वर्गीकृत हो रहा है…', bn: 'শ্রেণীবদ্ধ হচ্ছে…' },
    'home.no.image.err':      { en: 'Please select an image first.', hi: 'कृपया पहले एक छवि चुनें।', bn: 'আগে একটি ছবি নির্বাচন করুন।' },
    'home.detect.eyebrow':    { en: 'Detectable Conditions', hi: 'पहचानने योग्य स्थितियां', bn: 'শনাক্তযোগ্য অবস্থা' },
    'home.detect.title1':     { en: 'What We',           hi: 'हम क्या',            bn: 'আমরা কী' },
    'home.detect.title2':     { en: 'Detect',            hi: 'पहचानते हैं',        bn: 'শনাক্ত করি' },
    'home.card1.title':       { en: 'Healthy Leaf',      hi: 'स्वस्थ पत्ती',        bn: 'সুস্থ পাতা' },
    'home.card1.desc':        { en: 'No infection detected. Leaf structure, color, and tissue are within normal parameters. Continue standard care routine.', hi: 'कोई संक्रमण नहीं। पत्ती की संरचना, रंग और ऊतक सामान्य हैं। नियमित देखभाल जारी रखें।', bn: 'কোনো সংক্রমণ নেই। পাতার গঠন, রঙ ও টিস্যু স্বাভাবিক। নিয়মিত যত্ন চালিয়ে যান।' },
    'home.card1.threat':      { en: 'Threat Level',      hi: 'खतरे का स्तर',       bn: 'হুমকির মাত্রা' },
    'home.card2.title':       { en: 'Early Blight',      hi: 'प्रारंभिक झुलसा',    bn: 'আর্লি ব্লাইট' },
    'home.card2.desc':        { en: 'Caused by Alternaria solani. Characterized by dark circular spots with concentric rings. Spreads rapidly in warm, humid conditions.', hi: 'Alternaria solani से होता है। गर्म, आर्द्र स्थितियों में तेज़ी से फैलता है।', bn: 'Alternaria solani দ্বারা সৃষ্ট। উষ্ণ, আর্দ্র অবস্থায় দ্রুত ছড়ায়।' },
    'home.card3.title':       { en: 'Late Blight',       hi: 'देर से झुलसा',        bn: 'লেট ব্লাইট' },
    'home.card3.desc':        { en: 'Caused by Phytophthora infestans. Water-soaked lesions rapidly turning brown. The fungus behind the Irish Potato Famine.', hi: 'Phytophthora infestans से होता है। आयरिश आलू अकाल के पीछे का कवक।', bn: 'Phytophthora infestans দ্বারা সৃষ্ট। আইরিশ আলু দুর্ভিক্ষের পেছনের ছত্রাক।' },
    'home.how.eyebrow':       { en: 'Process',           hi: 'प्रक्रिया',           bn: 'প্রক্রিয়া' },
    'home.how.title1':        { en: 'How It',            hi: 'यह कैसे',             bn: 'এটি কীভাবে' },
    'home.how.title2':        { en: 'Works',             hi: 'काम करता है',         bn: 'কাজ করে' },
    'home.step1.title':       { en: 'Capture',           hi: 'तस्वीर लें',          bn: 'তোলো' },
    'home.step1.desc':        { en: 'Photograph the potato leaf clearly in natural light. Close-up shots work best.', hi: 'प्राकृतिक रोशनी में आलू की पत्ती की स्पष्ट तस्वीर लें।', bn: 'প্রাকৃতিক আলোয় আলু পাতার স্পষ্ট ছবি তুলুন।' },
    'home.step2.title':       { en: 'Upload',            hi: 'अपलोड करें',          bn: 'আপলোড করুন' },
    'home.step2.desc':        { en: 'Drag & drop or browse to upload. We accept JPG, PNG, and WEBP formats.', hi: 'ड्रैग करें या ब्राउज़ करें। JPG, PNG और WEBP स्वीकार किए जाते हैं।', bn: 'ড্র্যাগ করুন বা ব্রাউজ করুন। JPG, PNG ও WEBP গ্রহণযোগ্য।' },
    'home.step3.title':       { en: 'Analyze',           hi: 'विश्लेषण करें',        bn: 'বিশ্লেষণ করুন' },
    'home.step3.desc':        { en: 'Our CNN model processes the image against thousands of trained leaf samples.', hi: 'हमारा CNN मॉडल हजारों प्रशिक्षित नमूनों के विरुद्ध छवि संसाधित करता है।', bn: 'আমাদের CNN মডেল হাজারো প্রশিক্ষিত নমুনার সাথে ছবি প্রক্রিয়া করে।' },
    'home.step4.title':       { en: 'Diagnose',          hi: 'निदान करें',           bn: 'নির্ণয় করুন' },
    'home.step4.desc':        { en: 'Receive instant diagnosis with confidence score and treatment recommendation.', hi: 'आत्मविश्वास स्कोर और उपचार सुझाव के साथ तुरंत निदान प्राप्त करें।', bn: 'আত্মবিশ্বাস স্কোর ও চিকিৎসা পরামর্শ সহ তাৎক্ষণিক রোগ নির্ণয় পান।' },
    'home.footer.powered':    { en: 'Powered by DebIsh', hi: 'DebIsh द्वारा संचालित', bn: 'DebIsh দ্বারা চালিত' },
    'home.nav.logout':        { en: 'Logout',            hi: 'लॉग आउट',             bn: 'লগ আউট' },
    'home.trial.badge':       { en: 'TRIAL',             hi: 'ट्रायल',              bn: 'ট্রায়াল' },

    // ── LANGUAGE SWITCHER ────────────────────────────────────
    'lang.en': { en: 'EN', hi: 'EN', bn: 'EN' },
    'lang.hi': { en: 'HI', hi: 'HI', bn: 'HI' },
    'lang.bn': { en: 'BN', hi: 'BN', bn: 'BN' },
  };

  // ── State ────────────────────────────────────────────────────
  let currentLang = localStorage.getItem('ps_lang') || 'en';

  // ── Core translate function ──────────────────────────────────
  function t(key, lang) {
    const l = lang || currentLang;
    if (!translations[key]) {
      console.warn(`[i18n] Missing key: ${key}`);
      return key;
    }
    return translations[key][l] || translations[key]['en'] || key;
  }

  // ── Apply all translations in DOM ────────────────────────────
  function applyTranslations(lang) {
    currentLang = lang;
    localStorage.setItem('ps_lang', lang);

    // Update all [data-i18n] elements (text content)
    document.querySelectorAll('[data-i18n]').forEach(el => {
      el.textContent = t(el.dataset.i18n, lang);
    });

    // Update all [data-i18n-html] elements (innerHTML — for bold/em tags)
    document.querySelectorAll('[data-i18n-html]').forEach(el => {
      el.innerHTML = t(el.dataset.i18nHtml, lang);
    });

    // Update all [data-i18n-ph] elements (placeholder)
    document.querySelectorAll('[data-i18n-ph]').forEach(el => {
      el.placeholder = t(el.dataset.i18nPh, lang);
    });

    // Update lang switcher active state
    document.querySelectorAll('.lang-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.lang === lang);
    });

    // Update html lang attribute
    document.documentElement.lang = lang;

    // Trigger custom event for pages that need post-translation logic
    document.dispatchEvent(new CustomEvent('i18n:applied', { detail: { lang } }));
  }

  // ── Language Switcher Widget HTML ─────────────────────────────
  function renderSwitcher(container) {
    if (!container) return;
    container.innerHTML = `
      <div class="lang-switcher">
        <button class="lang-btn${currentLang==='en'?' active':''}" data-lang="en">EN</button>
        <button class="lang-btn${currentLang==='hi'?' active':''}" data-lang="hi">हि</button>
        <button class="lang-btn${currentLang==='bn'?' active':''}" data-lang="bn">বাং</button>
      </div>
    `;
    container.querySelectorAll('.lang-btn').forEach(btn => {
      btn.addEventListener('click', () => applyTranslations(btn.dataset.lang));
    });
  }

  // ── Init ─────────────────────────────────────────────────────
  function init() {
    // Render switcher into any .lang-switcher-slot elements
    document.querySelectorAll('.lang-switcher-slot').forEach(slot => renderSwitcher(slot));
    // Apply saved/default language
    applyTranslations(currentLang);
  }

  return { t, init, applyTranslations, currentLang: () => currentLang };
})();

// Auto-init when DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', i18n.init);
} else {
  i18n.init();
}