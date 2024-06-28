const pwShowHide = document.querySelectorAll(".showHidePw"),
    pwFields = document.querySelectorAll(".password");

//   js code to show/hide password and change icon
pwShowHide.forEach(eyeIcon => {
    eyeIcon.addEventListener("click", () => {
        pwFields.forEach(pwField => {
            if (pwField.type === "password") {
                pwField.type = "text";

                pwShowHide.forEach(icon => {
                    icon.classList.replace("bx-hide", "bx-show");
                })
            } else {
                pwField.type = "password";

                pwShowHide.forEach(icon => {
                    icon.classList.replace("bx-show", "bx-hide");
                })
            }
        })
    })
})

// js code to appear signup and login form
// signUp.addEventListener("click", () => {
//     container.classList.add("active");
// });
// login.addEventListener("click", () => {
//     container.classList.remove("active");
// });
