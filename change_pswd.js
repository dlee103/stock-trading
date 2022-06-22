//Initializing the variables from the document object
const form = document.querySelector("#change_pswd");
const password_1 = document.querySelector("#password_1");
const password_2 = document.querySelector("#password_2");

//getting the length of the password input box
let box_length = password_2.clientWidth;

//getting the list of all objects with the "msg" class and changing its length
let msg = document.querySelectorAll(".msg");
for (let i = 0, l = msg.length; i < l; i++) {
    msg[i].clientWidth = box_length;
}

//function making the input border red and displaying an error message
function showError(input, message)
{
    //get the parent element of the input that encompasses both the
    //input tag and message tag
    const parentDiv = input.parentElement;

    //removing the success class from the div and adding the error class
    //these classes change the border color
    parentDiv.classList.remove("success");
    parentDiv.classList.add("error");

    // display the error message using the small tag with the class "msg"
    const error = parentDiv.querySelector('.msg');
    error.textContent = message;
}

//function making the input border green and displaying an error message
function showSuccess(input, message)
{
    //get the parent element of the input that encompasses both the
    //input tag and message tag
    const parentDiv = input.parentElement;

    //removing the error class from the div and adding the success class
    //these classes change the border color
    parentDiv.classList.remove("error");
    parentDiv.classList.add("success");

    // display the success message using the small tag with the class "msg"
    parentDiv.querySelector('.msg').textContent = message;
}

//function to check if the input is blank
function isBlank(input)
{
    //if the input is blank the function returns true
    return (input ? false : true);
    /*Another way to put this is
    if (input)
    {
        return true
    }
    else
    {
        return false
    }*/
}

//using regex to search if password is secure
//Minimum eight characters, at least one uppercase letter, one lowercase letter, one number and one special character
function checkSecurePassword(password) {
    const re = new RegExp("^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[!@#\$%\^&\*])(?=.{8,})");
    return re.test(password)
}

//function checking whether the passwords match
function checkPassword(p1, p2)
{
    let valid = false;

    //getting the input values
    const password = password_1.value.trim();
    const confirmPassword = password_2.value.trim();

    //check if user input is blank
    if (isBlank(password))
    {
        showError(password_1, "Please enter new password");
    }

    else if (isBlank(confirmPassword))
    {
        showError(password_2, "Please re-enter new password");
    }

    //check if passwords are equal
    else if (password != confirmPassword)
    {
        showError(password_2, "Passwords do not match");
        showError(password_1, "");
    }

    //check if passwords are correct length and have a special character and a capital letter
    /*else if (checkSecurePassword(password_1)) {
        showError(password_2, "Password must be at least 8 characters and contain at least 1 lowercase character, 1 uppercase character, 1 number, and 1 special character")
    }*/

    else {
        showSuccess(password_1, "");
        showSuccess(password_2, "");
        valid = true;
    }

    return valid;
}

form.addEventListener("submit", function(event)
{
    //clear the previous session
    /*parentDiv.classList.remove("error");
    parentDiv.classList.remove("success");*/
    //LOOP THRU EVERY DIV WITH CLASS form-control and remove error and success classes

    // Prevent the form from submitting
    event.preventDefault();

    //check if the password is valid
    let isPasswordValid = checkPassword(password_1, password_2);

    if (isPasswordValid)
    {
        form.submit();
    }
})

//some code that I found online
//delays the response to x amount of seconds
const debounce = (fn, delay = 1000) => {
    let timeoutId;
    return (...args) => {
        // cancel the previous timer
        if (timeoutId) {
            clearTimeout(timeoutId);
        }
        // setup a new timer
        timeoutId = setTimeout(() => {
            fn.apply(null, args)
        }, delay);
    };
};

form.addEventListener("input", debounce(function(event)
{

    //Don't need to use the switch case for now...
    /*switch (event.target.id)
    {
        case "password_1":

        case "password_2"
    }*/

    //use an input event listener for when the user starts typing in the "confirm password" box
    /*doesnt make sense to also put it on the "New Password" box since it doesnt give the user
    a chance to confirm the password*/
    if (event.target.id == "password_2")
    {
        let isPasswordValid = checkPassword(password_1, password_2);
    }

}))