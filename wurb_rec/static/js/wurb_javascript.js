
window.onload = function () {
  // Define global variables.

  // Recording unit tile.

  //rec_start_button_id
  //rec_stop_button_id
  rec_status_id = document.getElementById("rec_status_id");
  rec_info_id = document.getElementById("rec_info_id");
  rec_detector_time_id = document.getElementById("rec_detector_time_id");

  // Geographic position tile.
  latitude_id = document.getElementById("latitude_id");
  longitude_id = document.getElementById("longitude_id");

  // Settings tile.
  tab_settings_basic_id = document.getElementById("tab_settings_basic_id");
  tab_settings_more_id = document.getElementById("tab_settings_more_id");
  tab_settings_scheduler_id = document.getElementById("tab_settings_scheduler_id");
  div_settings_basic_id = document.getElementById("div_settings_basic_id");
  div_settings_more_id = document.getElementById("div_settings_more_id");
  div_settings_scheduler_id = document.getElementById("div_settings_scheduler_id");

  // Recorded files tile.


  // Start websocket.
  var ws_url = (window.location.protocol === "https:") ? "wss://" : "ws://"
  ws_url += window.location.host // Note: Host includes port.
  ws_url += "/ws";
  startWebsocket(ws_url);

  // Start geolocation:
  startWatchPosition();
}

// Utils.

function hide_div(div_id) {
  div_id.style.visibility = "hidden";
  div_id.style.overflow = "hidden";
  div_id.style.height = "0";
  div_id.style.width = "0";
}

function show_div(div_id) {
  div_id.style.visibility = null;
  div_id.style.overflow = null;
  div_id.style.height = null;
  div_id.style.width = null;
}

function hide_show_settings_tabs(tab_name) {
  tab_settings_basic_id.classList.remove("is-active");
  tab_settings_more_id.classList.remove("is-active");
  tab_settings_scheduler_id.classList.remove("is-active");
  hide_div(div_settings_basic_id)
  hide_div(div_settings_more_id)
  hide_div(div_settings_scheduler_id)

  if (tab_name == "basic") {
    tab_settings_basic_id.classList.add("is-active");
    show_div(div_settings_basic_id)
  } else if (tab_name == "more") {
    tab_settings_more_id.classList.add("is-active");
    show_div(div_settings_more_id)
  } else if (tab_name == "scheduler") {
    tab_settings_scheduler_id.classList.add("is-active");
    show_div(div_settings_scheduler_id)
  }
}

async function callRecordingUnit(action) {
  try {
    document.getElementById("rec_status_id").innerHTML = "Waiting...";
    await fetch(action);
  } catch (err) {
    console.log(err);
  }
}

function startWatchPosition() {
  if (navigator.geolocation) {
    // navigator.geolocation.getCurrentPosition(showPosition);
    navigator.geolocation.watchPosition(showPosition);
    // navigator.geolocation.clearWatch(showPosition);
  } else {
    rec_info_id.innerHTML = "Geolocation is not supported by this browser.";
  }
}
function showPosition(position) {
  latitude_id.value = position.coords.latitude;
  longitude_id.value = position.coords.longitude;
}

async function setPosition() {
  try {
    var latitude_value = latitude_id.value;
    var longitude_value = longitude_id.value;
    // var url_string = "/set_position/?latitude=" + latitude_value + "&longitude=" + longitude_value;
    var url_string = `/set_position/?latitude=${latitude_value}&longitude=${longitude_value}`;
    await fetch(url_string);
  } catch (err) {
    console.log(err);
  }
}

async function setDetectorTime() {
  try {
    var posix_time_ms = new Date().getTime();
    var url_string = "/set_time/?posix_time_ms=" + posix_time_ms;    
    await fetch(url_string);
  } catch (err) {
    console.log(err);
  }
}


function startWebsocket(ws_url) {
  // var ws = new WebSocket("ws://localhost:8000/ws");
  var ws = new WebSocket(ws_url);
  ws.onmessage = function (event) {
    var data_json = JSON.parse(event.data);
    document.getElementById("rec_status_id").innerHTML = data_json.rec_status;
    document.getElementById("rec_info_id").innerHTML = data_json.device_name;
    document.getElementById("rec_detector_time_id").innerHTML = data_json.detector_time;
  };
  ws.onclose = function () {
    // Try to reconnect in 5th seconds. Will continue...
    ws = null;
    setTimeout(function () { startWebsocket(ws_url) }, 5000);
  };
}
