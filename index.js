const express = require('express');
const app = express();
const path = require('path');
const port=3000;

app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));
app.use(express.static(path.join(__dirname, 'public')));
app.use(express.urlencoded({ extended: true }));

app.get("/",(req,res)=>{
    res.render("login.ejs");
});
app.get("/home",(req,res)=>{
    res.render("index.ejs");
});
app.get("/signup",(req,res)=>{
    res.render("signup.ejs");
});













app.listen(port, () => {
    console.log(`Server is running on port ${port}`);
});