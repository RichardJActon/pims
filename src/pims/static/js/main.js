$( document ).ready(function() {
    // Action when they log in
    $("#login").click(process_login)
    $("#password").keypress(function(e){
        if(e.keyCode == 13){
            process_login();
        }
    });


    // Action when they log out
    $("#logout").click(logout)

})

function logout() {
    Cookies.remove("pims_session_id")
    location.reload()
}




function process_login() {
    let username = $("#username").val()
    let password = $("#password").val()

    // Clear the password so they can't do it again
    $("#password").val("")

    // Add a spinner so they know it's trying!
    $("#login").html(`<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Checking`)
    $("#login").prop("disabled",true)
    $("#username").prop("disabled",true)
    $("#password").prop("disabled",true)


    $.ajax(
        {
            url: "processlogin",
            method: "POST",
            data: {
                username: username,
                password: password
            },
            success: function(session_string) {
                window.location.href = "/"
            },
            error: function(message) {
                $("#login").prop("disabled",false)
                $("#username").prop("disabled",false)
                $("#password").prop("disabled",false)
                $("#login").text("Login Failed")
                $("#login").removeClass("btn-primary")
                $("#login").addClass("btn-danger")
                setTimeout(function(){
                    $("#login").text("Log In")
                    $("#login").removeClass("btn-danger")
                    $("#login").addClass("btn-primary")
                    },2000)
            }
        }
    )
}

