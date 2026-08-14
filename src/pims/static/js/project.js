$( document ).ready(function() {

    $("#add_sample").click(show_new_sample)
    $(".editsample").click(show_new_sample)
    $("#save_sample").click(save_sample)
    $(".deletesample").click(delete_sample)

})




function delete_sample() {
    //  We need to get the project id and sample id from 
    // the start of the table row in which the delete 
    // button was found.

    let ids = $(this).parent().parent().find("td").first().text()
    let project_sample = ids.split("-")

    $(this).prop("disabled",true)

    let row_to_delete = $(this).parent().parent()
    $.ajax(
        {
            url: "/deletesample",
            method: "POST",
            data: {
                project_id: project_sample[0],
                sample_id: project_sample[1]
            },
            success: function() {
                row_to_delete.remove()
            },
            error: function(message) {
                $(this).prop("disabled",false)
                console.log("Failed to delete sample")
                return        
            }
        }
    )



}


function save_sample() {
    // We need the project id
    let project_id = location.pathname.split("/").pop()
    if (project_id == "project") {
        project_id = ""
    }

    // We need to determine if this is a new sample or editing an existing one
    let sample_id = $("#sample_modal_header").data("sample_id")

    let something_failed = false

    // We need to collect the standard features
    let name = $("#sample_name").val().trim()
    if (name) {
         $("#sample_name").css("border-color","rgb(222, 226, 230")
    }
    else {
        $("#sample_name").css("border-color","red")
        something_failed = true
    }

    let state = $("#sample_state").val().trim()
    if (state) {
         $("#sample_state").css("border-color","rgb(222, 226, 230")
    }
    else {
        $("#sample_state").css("border-color","red")
        something_failed = true
    }

    let organism = $("#organism").val().trim()
    if (organism) {
         $("#organism").css("border-color","rgb(222, 226, 230")
    }
    else {
        $("#organism").css("border-color","red")
        something_failed = true
    }
    
    // We then need the values for the tags
    let tag_values = []
    $(".tag_value_input").each(function(){
        let value = $(this).val().trim()
        if (value) {
            $(this).css("border-color","rgb(222, 226, 230")
            tag_values.push(value)
        }
        else {
            $(this).css("border-color","red")
            something_failed = true
        }
    })

    if (something_failed) {
        return
    }

    // Now we can add/edit this
    $("#save_sample").prop("disabled",true)
    $.ajax(
        {
            url: "/savesample",
            method: "POST",
            data: {
                project_id: project_id,
                sample_id: sample_id,
                name: name,
                state: state,
                organism: organism,
                tags: tag_values
            },
            success: function(project_id) {
                window.location.reload()
            },
            error: function(message) {
                $("#errormessage").text("Failed to save project")
                $("#editprojecterror").modal("show")
                $("#save_sample").prop("disabled",false)
                return        
            }
        }
    )


}


function show_new_sample() {

    // We might have come from the "new sample" button, or we might
    // be editing an existing sample

    let input_fields = $("#editsamplediv").find("input")

    if ($(this).hasClass("editsample")) {
        // We're editing an existing sample

        let row_data = $(this).parent().parent().find("td")

        $("#sample_modal_header").text("Edit Sample "+row_data.eq(0).text())

        let project_sample = row_data.eq(0).text().split("-")
        $("#sample_modal_header").data("sample_id",project_sample[1])

        for (i=0;i<input_fields.length;i++) {
            input_fields.eq(i).val(row_data.eq(i+1).text().trim())
        }

    }
    else {
        // We're starting a new sample
        input_fields.val("")
        $("#sample_modal_header").data("sample_id","")
        $("#sample_modal_header").text("Add Sample")
    }

    // Blank the contents
    $("#editsamplediv").modal("show")
}