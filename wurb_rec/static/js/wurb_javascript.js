
window.onload = function () {
  // Define global variables.

  // Recording unit tile.
  var rec_start_button_id = document.getElementById("rec_start_button_id");
  var rec_stop_button_id = document.getElementById("rec_stop_button_id");
  var rec_status_id = document.getElementById("rec_status_id");
  var rec_info_id = document.getElementById("rec_info_id");
  var rec_detector_time_id = document.getElementById("rec_detector_time_id");
  var rec_log_table_id = document.getElementById("rec_log_table_id");

  // Geographic position tile.
  var geo_source_option_id = document.getElementById("geo_source_option_id");
  var geo_latitude_id = document.getElementById("geo_latitude_id");
  var geo_longitude_id = document.getElementById("geo_longitude_id");
  var geo_set_pos_button_id = document.getElementById("geo_set_pos_button_id");
  var geo_set_time_button_id = document.getElementById("geo_set_time_button_id");

  // Settings tile.
  var tab_settings_basic_id = document.getElementById("tab_settings_basic_id");
  var tab_settings_more_id = document.getElementById("tab_settings_more_id");
  var tab_settings_scheduler_id = document.getElementById("tab_settings_scheduler_id");
  var div_settings_basic_id = document.getElementById("div_settings_basic_id");
  var div_settings_more_id = document.getElementById("div_settings_more_id");
  var div_settings_scheduler_id = document.getElementById("div_settings_scheduler_id");

  var settings_default_latitude_id = document.getElementById("settings_default_latitude_id");
  var settings_default_longitude_id = document.getElementById("settings_default_longitude_id");

  // Recorded files tile.


  // Start websocket.
  var ws_url = (window.location.protocol === "https:") ? "wss://" : "ws://"
  ws_url += window.location.host // Note: Host includes port.
  ws_url += "/ws";
  startWebsocket(ws_url);

  // Check geolocation:
  geoLocationSourceOnChange();
};

// Utils.

function hide_div(div_id) {
  div_id.style.visibility = "hidden";
  div_id.style.overflow = "hidden";
  div_id.style.height = "0";
  div_id.style.width = "0";
};

function show_div(div_id) {
  div_id.style.visibility = null;
  div_id.style.overflow = null;
  div_id.style.height = null;
  div_id.style.width = null;
};

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
  };
};

function geoLocationSourceOnChange(val) {
  // alert("geoSourceOnChange: " + val);
  geo_latitude_id.value = settings_default_latitude_id.value
  geo_longitude_id.value = settings_default_longitude_id.value
  if (val == "geo-default") {
    geo_latitude_id.disabled = true;
    geo_longitude_id.disabled = true;
    geo_set_pos_button_id.disabled = false;
    geo_set_time_button_id.disabled = false;
  }
  else if (val == "geo-manually") {
    geo_latitude_id.disabled = false;
    geo_longitude_id.disabled = false;
    geo_set_pos_button_id.disabled = false;
    geo_set_time_button_id.disabled = false;
  }
  else if (val == "geo-client-gps") {
    activateGeoLocation()
    geo_latitude_id.disabled = true;
    geo_longitude_id.disabled = true;
    geo_set_pos_button_id.disabled = false;
    geo_set_time_button_id.disabled = false;
  }
  else if (val == "geo-usb-gps") {
    geo_latitude_id.disabled = true;
    geo_longitude_id.disabled = true;
    geo_set_pos_button_id.disabled = true;
    geo_set_time_button_id.disabled = true;
    alert(`Sorry, USB-GPS not implemented yet.`);
  }
  else {
    geo_latitude_id.disabled = true;
    geo_longitude_id.disabled = true;
    geo_set_pos_button_id.disabled = true;
    geo_set_time_button_id.disabled = true;
  }
}

function activateGeoLocation() {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(showPosition, errorCallback, { timeout: 10000 });
    // navigator.geolocation.getCurrentPosition(showPosition);
    // // navigator.geolocation.watchPosition(showPosition);
    // // navigator.geolocation.clearWatch(showPosition);
  } else {
    alert(`Geo position from client:\nNot supported by this browser.`);
  };
};
function showPosition(position) {
  rec_info_id.innerHTML = position.coords.latitude;
  latitude_id.value = position.coords.latitude;
  longitude_id.value = position.coords.longitude;
};
function errorCallback(error) {
  alert(`Geo position from client:\nERROR(${error.code}): ${error.message}`);
};


async function callRecordingUnit(action) {
  try {
    document.getElementById("rec_status_id").innerHTML = "Waiting...";
    await fetch(action);
  } catch (err) {
    alert(`ERROR callRecordingUnit: ${err}`);
    console.log(err);
  };
};

async function setPosition() {
  try {
    let latitude_value = geo_latitude_id.value;
    let longitude_value = geo_longitude_id.value;
    // var url_string = "/set_position/?latitude=" + latitude_value + "&longitude=" + longitude_value;
    let url_string = `/set_position/?latitude=${latitude_value}&longitude=${longitude_value}`;
    await fetch(url_string);
  } catch (err) {
    alert(`ERROR setPosition: ${err}`);
    console.log(err);
  };
};


async function setDetectorTime() {
  try {
    let posix_time_ms = new Date().getTime();
    // let url_string = "/set_time/?posix_time_ms=" + posix_time_ms;    
    let url_string = `/set_time/?posix_time_ms=${posix_time_ms}`;
    await fetch(url_string);
  } catch (err) {
    alert(`ERROR setDetectorTime: ${err}`);
    console.log(err);
  };
};


function startWebsocket(ws_url) {
  // var ws = new WebSocket("ws://localhost:8000/ws");
  var ws = new WebSocket(ws_url);
  ws.onmessage = function (event) {
    var data_json = JSON.parse(event.data);
    document.getElementById("rec_status_id").innerHTML = data_json.rec_status;
    document.getElementById("rec_info_id").innerHTML = data_json.device_name;
    document.getElementById("rec_detector_time_id").innerHTML = data_json.detector_time;

    document.getElementById("rec_log_table_id").innerHTML =
      "<tr><td>23:45:47 TEST-Recording stopped.</td>";

  }
  ws.onclose = function () {
    // Try to reconnect in 5th seconds. Will continue...
    ws = null;
    setTimeout(function () { startWebsocket(ws_url) }, 5000);
  };
};
