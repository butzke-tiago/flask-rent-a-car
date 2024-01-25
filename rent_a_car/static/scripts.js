function validateForm(form) {
    for (let input of document.forms[form]) {
        console.log(input)
        if (input.value == "" || input.value == "None") {
            input.disabled = true;
        }
    }
}
function sendDeleteRequest(url, next) {
    fetch(`${url}`, {
        method: 'DELETE',
        headers: {
            'Accept': '*/*'
        },
    })
        .then(response => {
            if (response.ok) {
                // Handle successful response
                console.log('Delete request successful');
                if (response.redirected) {
                    next = response.url
                }
            } else {
                // Handle error response
                console.error('Delete request failed');
                console.log(response.status);
                if (response.redirected) {
                    next = response.url
                }
            }
        })
        .catch(error => {
            // Handle network error
            console.error('An error occurred:', error);
        })
        .finally(() => {
            location.href = next;
        });
}

function loadImageFromUrlToDiv(url_field, image_div, height) {
    var url = document.getElementById(url_field).value;
    var div = document.createElement('div');
    div.className = "imageWrapper";
    var img = document.createElement('img');
    img.src = url;
    img.height = height
    div.appendChild(img);
    while (document.getElementById(image_div).firstChild)
        document.getElementById(image_div).removeChild(document.getElementById(image_div).firstChild);
    document.getElementById(image_div).appendChild(div);
    return false;
}