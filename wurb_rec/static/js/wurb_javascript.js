
window.onload = function () {
  // Define global variables.

  // Recording unit tile.
  const rec_start_button_id = document.getElementById("rec_start_button_id");
  const rec_stop_button_id = document.getElementById("rec_stop_button_id");
  const rec_status_id = document.getElementById("rec_status_id");
  const rec_info_id = document.getElementById("rec_info_id");
  const rec_detector_time_id = document.getElementById("rec_detector_time_id");
  const rec_log_table_id = document.getElementById("rec_log_table_id");

  // Geographic location tile.
  const geo_source_option_id = document.getElementById("geo_source_option_id");
  const latitude_dd_id = document.getElementById("latitude_dd_id");
  const longitude_dd_id = document.getElementById("longitude_dd_id");
  const geo_set_pos_button_id = document.getElementById("geo_set_pos_button_id");
  const geo_set_time_button_id = document.getElementById("geo_set_time_button_id");

  // Settings tile. Tab hide/show.
  const tab_settings_basic_id = document.getElementById("tab_settings_basic_id");
  const tab_settings_more_id = document.getElementById("tab_settings_more_id");
  const tab_settings_scheduler_id = document.getElementById("tab_settings_scheduler_id");
  const div_settings_basic_id = document.getElementById("div_settings_basic_id");
  const div_settings_more_id = document.getElementById("div_settings_more_id");
  const div_settings_scheduler_id = document.getElementById("div_settings_scheduler_id");
  // Fields and buttons.
  const settings_rec_mode_id = document.getElementById("settings_rec_mode_id");
  const settings_filename_prefix_id = document.getElementById("settings_filename_prefix_id");
  const settings_detection_limit_id = document.getElementById("settings_detection_limit_id");
  const settings_detection_sensitivity_id = document.getElementById("settings_detection_sensitivity_id");
  const settings_file_directory_id = document.getElementById("settings_file_directory_id");
  const settings_detection_algorithm_id = document.getElementById("settings_detection_algorithm_id");
  const settings_scheduler_start_event_id = document.getElementById("settings_scheduler_start_event_id");
  const settings_scheduler_start_adjust_id = document.getElementById("settings_scheduler_start_adjust_id");
  const settings_scheduler_stop_event_id = document.getElementById("settings_scheduler_stop_event_id");
  const settings_scheduler_stop_adjust_id = document.getElementById("settings_scheduler_stop_adjust_id");
  const settings_save_button_id = document.getElementById("settings_save_button_id");
  const settings_reset_button_id = document.getElementById("settings_reset_button_id");
  const settings_default_button_id = document.getElementById("settings_default_button_id");

  // Update stored location and settings.
  getLocation()
  getSettings()
  // Check geolocation:
  geoLocationSourceOnChange();

  // Start websocket.
  var ws_url = (window.location.protocol === "https:") ? "wss://" : "ws://"
  ws_url += window.location.host // Note: Host includes port.
  ws_url += "/ws";
  startWebsocket(ws_url);
};

function hideDivision(div_id) {
  if (div_id != 'undefined') {
    div_id.style.visibility = "hidden";
    div_id.style.overflow = "hidden";
    div_id.style.height = "0";
    div_id.style.width = "0";
  }
};

function showDivision(div_id) {
  if (div_id != 'undefined') {
    div_id.style.visibility = null;
    div_id.style.overflow = null;
    div_id.style.height = null;
    div_id.style.width = null;
  }
};

function hideShowSettingsTabs(tab_name) {
  tab_settings_basic_id.classList.remove("is-active");
  tab_settings_more_id.classList.remove("is-active");
  tab_settings_scheduler_id.classList.remove("is-active");
  hideDivision(div_settings_basic_id)
  hideDivision(div_settings_more_id)
  hideDivision(div_settings_scheduler_id)

  if (tab_name == "basic") {
    tab_settings_basic_id.classList.add("is-active");
    showDivision(div_settings_basic_id)
  } else if (tab_name == "more") {
    tab_settings_more_id.classList.add("is-active");
    showDivision(div_settings_more_id)
  } else if (tab_name == "scheduler") {
    tab_settings_scheduler_id.classList.add("is-active");
    showDivision(div_settings_scheduler_id)
  };
};

function geoLocationSourceOnChange() {
  let selected_value = geo_source_option_id.options[geo_source_option_id.selectedIndex].value
  if (selected_value == "geo-not-used") {
    latitude_dd_id.value = "0.0";
    longitude_dd_id.value = "0.0";
    latitude_dd_id.disabled = true;
    longitude_dd_id.disabled = true;
    geo_set_pos_button_id.disabled = false;
    geo_set_time_button_id.disabled = false;
  }
  else if (selected_value == "geo-manual") {
    latitude_dd_id.disabled = false;
    longitude_dd_id.disabled = false;
    geo_set_pos_button_id.disabled = false;
    geo_set_time_button_id.disabled = false;
  }
  else if (selected_value == "geo-client-gps") {
    activateGeoLocation()
    latitude_dd_id.disabled = true;
    longitude_dd_id.disabled = true;
    geo_set_pos_button_id.disabled = false;
    geo_set_time_button_id.disabled = false;
  }
  else if (selected_value == "geo-usb-gps") {
    latitude_dd_id.disabled = true;
    longitude_dd_id.disabled = true;
    geo_set_pos_button_id.disabled = true;
    geo_set_time_button_id.disabled = true;
    alert(`Sorry, USB-GPS not implemented yet.`);
  }
  else {
    latitude_dd_id.disabled = true;
    longitude_dd_id.disabled = true;
    geo_set_pos_button_id.disabled = true;
    geo_set_time_button_id.disabled = false;
  }
}

function activateGeoLocation() {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(showPosition, errorCallback, { timeout: 10000 });
    // navigator.geolocation.getCurrentPosition(showLocation);
    // navigator.geolocation.watchPosition(showLocation);
    // navigator.geolocation.clearWatch(showLocation);
  } else {
    alert(`Geo location from client:\nNot supported by this browser.`);
  };
};
function showPosition(location) {
  rec_info_id.innerHTML = location.coords.latitude;
  latitude_id.value = location.coords.latitude;
  longitude_id.value = location.coords.longitude;
};
function errorCallback(error) {
  alert(`Geo location from client:\nERROR(${error.code}): ${error.message}`);
};

async function startRecording() {
  try {
    document.getElementById("rec_status_id").innerHTML = "Waiting...";
    // Save location and settings before recording starts.
    saveLocation()
    saveSettings()
    await fetch('/start-rec');
  } catch (err) {
    alert(`ERROR startRecording: ${err}`);
    console.log(err);
  };
};

async function stopRecording(action) {
  try {
    document.getElementById("rec_status_id").innerHTML = "Waiting...";
    await fetch('/stop-rec');
  } catch (err) {
    alert(`ERROR stopRecording: ${err}`);
    console.log(err);
  };
};

async function saveLocation() {
  try {
    let location = {
      geo_source_option: geo_source_option_id.value,
      latitude_dd: latitude_dd_id.value,
      longitude_dd: longitude_dd_id.value,
    }
    await fetch("/save-location/",
      {
        method: "POST",
        body: JSON.stringify(location)
      })
  } catch (err) {
    alert(`ERROR saveLocation: ${err}`);
    console.log(err);
  };
};

async function getLocation() {
  try {
    let response = await fetch("/get-location");
    let data = await response.json();
    updateLocation(data);
  } catch (err) {
    alert(`ERROR getLocation: ${err}`);
    console.log(err);
  };
};

async function setDetectorTime() {
  try {
    let posix_time_ms = new Date().getTime();
    // let url_string = "/set_time/?posixtime=" + posix_time_ms;    
    let url_string = `/set-time/?posixtime=${posix_time_ms}`;
    await fetch(url_string);
  } catch (err) {
    alert(`ERROR setDetectorTime: ${err}`);
    console.log(err);
  };
};

async function saveSettings() {
  try {
    let settings = {
      rec_mode: settings_rec_mode_id.value,
      filename_prefix: settings_filename_prefix_id.value,
      detection_limit: settings_detection_limit_id.value,
      detection_sensitivity: settings_detection_sensitivity_id.value,
      file_directory: settings_file_directory_id.value,
      detection_algorithm: settings_detection_algorithm_id.value,
      scheduler_start_event: settings_scheduler_start_event_id.value,
      scheduler_start_adjust: settings_scheduler_start_adjust_id.value,
      scheduler_stop_event: settings_scheduler_stop_event_id.value,
      scheduler_stop_adjust: settings_scheduler_stop_adjust_id.value,
    }
    await fetch("/save-settings/",
      {
        method: "POST",
        body: JSON.stringify(settings)
      })
  } catch (err) {
    alert(`ERROR saveSettings: ${err}`);
    console.log(err);
  };
};

async function getSettings() {
  try {
    let response = await fetch("/get-settings/?default=false");
    let data = await response.json();
    updateSettings(data);
  } catch (err) {
    alert(`ERROR getSettings: ${err}`);
    console.log(err);
  };
};

async function getDefaultSettings() {
  try {
    let response = await fetch("/get-settings/?default=true");
    let data = await response.json();
    updateSettings(data);
  } catch (err) {
    alert(`ERROR getDefaultSettings: ${err}`);
    console.log(err);
  };
};

async function raspberryPiControl(command) {
  try {
    let url_string = `/rpi-control/?command=${command}`;
    await fetch(url_string);
  } catch (err) {
    alert(`ERROR raspberryPiControl: ${err}`);
    console.log(err);
  };
};

function updateStatus(status) {
  rec_status_id.innerHTML = status.rec_status;
  rec_info_id.innerHTML = status.device_name;
  rec_detector_time_id.innerHTML = status.detector_time;
}

function updateLocation(location) {
  geo_source_option_id.value = location.geo_source_option
  latitude_dd_id.value = location.latitude_dd
  longitude_dd_id.value = location.longitude_dd
  // Check geolocation:
  geoLocationSourceOnChange();
}

function updateSettings(settings) {
  settings_rec_mode_id.value = settings.rec_mode
  settings_filename_prefix_id.value = settings.filename_prefix
  settings_detection_limit_id.value = settings.detection_limit
  settings_detection_sensitivity_id.value = settings.detection_sensitivity
  settings_file_directory_id.value = settings.file_directory
  settings_detection_algorithm_id.value = settings.detection_algorithm
  settings_scheduler_start_event_id.value = settings.scheduler_start_event
  settings_scheduler_start_adjust_id.value = settings.scheduler_start_adjust
  settings_scheduler_stop_event_id.value = settings.scheduler_stop_event
  settings_scheduler_stop_adjust_id.value = settings.scheduler_stop_adjust
}

function updateLogTable(log_rows) {
  // document.getElementById("rec_log_table_id").innerHTML =
  //   "<tr><td>23:45:47 TEST.</td>";
}

function startWebsocket(ws_url) {
  // let ws = new WebSocket("ws://localhost:8000/ws");
  let ws = new WebSocket(ws_url);
  ws.onmessage = function (event) {
    let data_json = JSON.parse(event.data);
    if ("status" in data_json === true) {
      updateStatus(data_json.status)
    }
    if ("location" in data_json === true) {
      updateLocation(data_json.location)
    }
    if ("settings" in data_json === true) {
      updateSettings(data_json.settings)
    }
    if ("log_rows" in data_json === true) {
      updateLogTable(data_json.log_rows)
    }
  }
  ws.onclose = function () {
    // Try to reconnect in 5th seconds. Will continue...
    ws = null;
    setTimeout(function () { startWebsocket(ws_url) }, 5000);
  };
};
