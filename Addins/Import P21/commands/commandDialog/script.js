// const name = document.getElementById(".adaptive");

function createPng() {
    var img = document.createElement("img");
    img.className = "toolImg";
    img.alt = "Tool PNG";
    img.src = data["pngLocation"];
    img.width = "100";
    img.height = "40";
    return img;
}
function updateDoc(e, jsonData) {
    // var items = document.getElementsByClassName("initial");
    // var data = JSON.parse(jsonData);
    // var type = data["Tool IsoType"];
    // var toolitems = [data["Tool Name"], data["Tool Description"]];

    // console.log(type)

    // var adp = document.getElementById("adaptive");
    // var collDiv = document.getElementById("collet");
    // var inner = document.getElementsByClassName("inner");
    // var div = document.getElementsByClassName("v1");
    // div.remove()
    // collDiv.remove();
    // adp.remove();
    // inner.remove();

    // if (type == "assembly item-collet") {
    //     items.item(0).appendChild(adp);
    //     items.item(0).appendChild(div);
    //     var td = document.createElement("b");
    //     td.className = "inner";
    //     if (data["pngLocation"]) {
    //         var img = document.createElement("img");
    //         img.className = "toolImg";
    //         img.alt = "Tool PNG";
    //         img.src = data["pngLocation"];
    //         img.width = "100";
    //         img.height = "40";
    //         td.appendChild(img);
    //     }
    //     for (var ti = 0; ti < toolitems.length; ++ti) {
    //         var tl = document.createElement("tl");
    //         tl.innerHTML = toolitems[ti];
    //         td.appendChild(tl);
    //     }
    //     items.item(0).appendChild(td);
    //     items.item(0).appendChild(div);
    //     items.item(0).appendChild(inner);
    // }
}

function changeDoc(e, jsonData) {
    var items = document.getElementsByClassName("initial");

    console.log(items);

    var addItems = ["ADD AADPTIVE ITEM", "ADD COLLET OR SLEEVE", "ADD CUTTING ITEM"];
    var data = JSON.parse(jsonData);

    var toolitems = [data["Tool Name"], data["Tool Description"]];

    for (var i = 0; i < addItems.length;  ++i) {
        var td1 = document.createElement("a");
        var type = data["Tool IsoType"];
        
        if (String(type).split("-")[0] == "mil" && i == 2) {
            var div = document.createElement("div");
            div.className = "vl";
            items.item(0).appendChild(div)

            var td = document.createElement("b");
            td.className = "inner";
            if (data["pngLocation"]) {
                var img = document.createElement("img");
                img.className = "toolImg";
                img.alt = "Tool PNG";
                img.src = data["pngLocation"];
                img.width = "100";
                img.height = "40";
                td.appendChild(img);
            }
            for (var ti = 0; ti < toolitems.length; ++ti) {
                var tl = document.createElement("tl");
                tl.innerHTML = toolitems[ti];
                td.appendChild(tl);
            }
            items.item(0).appendChild(td);
            continue
        } else if (type == "assembly item-collet" && i == 1) {
            var div = document.createElement("div");
            div.className = "vl";
            items.item(0).appendChild(div)

            var td = document.createElement("b");
            td.className = "inner";
            if (data["pngLocation"]) {
                var img = document.createElement("img");
                img.className = "toolImg";
                img.alt = "Tool PNG";
                img.src = data["pngLocation"];
                img.width = "100";
                img.height = "40";
                td.appendChild(img);
            }
            for (var ti = 0; ti < toolitems.length; ++ti) {
                var tl = document.createElement("tl");
                tl.innerHTML = toolitems[ti];
                td.appendChild(tl);
            }
            items.item(0).appendChild(td);
            continue;
        }

        td1.innerHTML += addItems[i];
        if (i == 0) {
            td1.id = "adaptive";
            td1.setAttribute("onclick", "request(this, 'adaptive')");
        } else if (i == 1) {
            td1.id = "collet";
            td1.setAttribute("onclick", "request(this, 'collet')");
        } else {
            td1.id = "cutting";
            td1.setAttribute("onclick", "request(this, 'cutting')");
        }
        

        items.item(0).appendChild(td1);
    }

}

function request(e, type) {
    if (type == "adaptive") {
        args = {"Req": "AdaptiveItem"};
    } else if (type == "collet") {
        args = {"Req": "ColletItem"};
    } else {
        args = {"Req": "CuttingItem"};
    }
    
    adsk.fusionSendData('request', JSON.stringify(args));
}


function sendInfoToFusion(e){
    var today = new Date();
    var dd = String(today.getDate()).padStart(2, '0');
    var mm = String(today.getMonth() + 1).padStart(2, '0');
    var yyyy = today.getFullYear();

    var hours = String(today.getHours()).padStart(2, '0');
    var minutes = String(today.getMinutes()).padStart(2, '0');
    var seconds = String(today.getSeconds()).padStart(2, '0');

    var date = dd + '/' + mm + '/' + yyyy;
    var time = hours + ':' + minutes + ':' + seconds;
    var args = {
        arg1 : "Sample argument 1",
        arg2 : "Sample argument 2"
    };
    adsk.fusionSendData('send', JSON.stringify(args));
}

window.fusionJavaScriptHandler = {handle: function(action, jsonData){
    try {
        if (action == 'update') {
            // Update a paragraph with the data passed in.
            changeDoc(this, jsonData)
        }
        else if (action == 'contentUpdate') {
            updateDoc(this, jsonData)
        }
        else if (action == 'debugger') {
            debugger;
        }
        else {
            return 'Unexpected command type: ' + action;
        }
    } catch (e) {
        console.log(e);
        console.log('exception caught with command: ' + action + ', data: ' + data);
    }
    return 'OK';
}};