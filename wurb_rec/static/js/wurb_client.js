
async function startRecording() {
  try {
    document.getElementById("detector_status_id").innerHTML = "Waiting...";
    // // Save settings before recording starts.
    // saveSettings()
    await fetch('/start-rec/');
  } catch (err) {
    alert(`ERROR startRecording: ${err}`);
    console.log(err);
  };
};

async function stopRecording() {
  try {
    document.getElementById("detector_status_id").innerHTML = "Waiting...";
    await fetch('/stop-rec/');
  } catch (err) {
    alert(`ERROR stopRecording: ${err}`);
    console.log(err);
  };
};

async function recModeOnChange() {
  try {
    let recmode = detector_mode_select_id.value;
    let url_string = `/save-rec-mode/?recmode=${recmode}`;
    await fetch(url_string);
  } catch (err) {
    alert(`ERROR recModeOnChange: ${err}`);
    console.log(err);
  };
};

async function saveLocationSource() {
  try {
    let location = {
      geo_source: location_source_select_id.value,
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

async function saveLocation() {
  try {
    let location = {
      geo_source: location_source_select_id.value,
      latitude_dd: latitude_dd_id.value,
      longitude_dd: longitude_dd_id.value,
    }
    if (location_source_select_id.value == "geo-manual") {
      location["manual_latitude_dd"] = latitude_dd_id.value
      location["manual_longitude_dd"] = longitude_dd_id.value
    }
    if (location_source_select_id.value == "geo-gps") {
      location["geo_source"] = "geo-manual"
      location["manual_latitude_dd"] = latitude_dd_id.value
      location["manual_longitude_dd"] = longitude_dd_id.value
    }
    if (location_source_select_id.value == "geo-gps-or-manual") {
      location["geo_source"] = "geo-manual"
      location["manual_latitude_dd"] = latitude_dd_id.value
      location["manual_longitude_dd"] = longitude_dd_id.value
    }
    if (location_source_select_id.value == "geo-last-gps-or-manual") {
      location["geo_source"] = "geo-manual"
      location["manual_latitude_dd"] = latitude_dd_id.value
      location["manual_longitude_dd"] = longitude_dd_id.value
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
    let response = await fetch("/get-location/");
    let data = await response.json();
    updateLocation(data);
  } catch (err) {
    alert(`ERROR getLocation: ${err}`);
    console.log(err);
  };
};

async function getManualLocation() {
  try {
    let response = await fetch("/get-location/");
    let location = await response.json();
    latitude_dd_id.value = location.manual_latitude_dd
    longitude_dd_id.value = location.manual_longitude_dd
  } catch (err) {
    alert(`ERROR getManualLocation: ${err}`);
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

async function saveSettings(settings_type) {
  try {
    let url_string = "/save-settings/";
    if (settings_type == "user-defined") {
      url_string = "/save-settings-user/";
    } 
    else if (settings_type == "startup") {
      url_string = "/save-settings-startup/";
    } 
    let settings = {
      rec_mode: detector_mode_select_id.value,
      file_directory: settings_file_directory_id.value,
      file_directory_date_option: settings_file_directory_date_option_id.value,
      filename_prefix: settings_filename_prefix_id.value,
      detection_limit_khz: settings_detection_limit_id.value,
      detection_sensitivity_dbfs: settings_detection_sensitivity_id.value,
      detection_algorithm: settings_detection_algorithm_id.value,
      rec_length_s: settings_rec_length_id.value,
      rec_type: settings_rec_type_id.value,
      feedback_on_off: settings_feedback_on_off_id.value,
      feedback_volume: feedback_volume_slider_id.value,
      feedback_pitch: feedback_pitch_slider_id.value,
      feedback_filter_low_khz: settings_feedback_filter_low_id.value,
      feedback_filter_high_khz: settings_feedback_filter_high_id.value,
      startup_option: settings_startup_option_id.value,
      scheduler_start_event: settings_scheduler_start_event_id.value,
      scheduler_start_adjust: settings_scheduler_start_adjust_id.value,
      scheduler_stop_event: settings_scheduler_stop_event_id.value,
      scheduler_stop_adjust: settings_scheduler_stop_adjust_id.value,
      scheduler_post_action: settings_scheduler_post_action_id.value,
      scheduler_post_action_delay: settings_scheduler_post_action_delay_id.value,
    }
    await fetch(url_string,
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

async function loadSettings(settings_type) {
  try {
    let response = await fetch("/load-settings/?settings_type=" + settings_type);
    await response.json();
  } catch (err) {
    alert(`ERROR getSettings: ${err}`);
    console.log(err);
  };
};

async function setAudioFeedback() {
  try {
    let volume = feedback_volume_slider_id.value;
    let pitch = feedback_pitch_slider_id.value;
    let url_string = `/set-audio-feedback/?volume=${volume}&pitch=${pitch}`;
    await fetch(url_string);
  } catch (err) {
    alert(`ERROR setAudioFeedback: ${err}`);
    console.log(err);
  };
};

async function manualTrigger() {
  try {
    let url_string = `/rec-manual-trigger/`;
    await fetch(url_string);
  } catch (err) {
    alert(`ERROR manualTrigger: ${err}`);
    console.log(err);
  };
};

async function raspberryPiControl(command) {
  try {
    if (command == "rpi_cancel") {
      detector_mode_select_id.value = last_used_settings.rec_mode
      modeSelectOnChange(update_detector = true)
    } else {
      detector_mode_select_id.value = last_used_settings.rec_mode
      modeSelectOnChange(update_detector = true)
      let url_string = `/rpi-control/?command=${command}`;
      await fetch(url_string);
    }
  } catch (err) {
    alert(`ERROR raspberryPiControl: ${err}`);
    console.log(err);
  };
};

let wait_text_nr = 0

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
    if ("latlong" in data_json === true) {
      updateLatLong(data_json.latlong)
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

    if (wait_text_nr == 0) { 
      wait_text = "Waiting for response from detector..."
    } else if (wait_text_nr == 1) {
      wait_text = "Waiting for response from detector."
    } else if (wait_text_nr == 2) {
      wait_text = "Waiting for response from detector.."
    }
    wait_text_nr += 1
    if (wait_text_nr >= 3) {
      wait_text_nr = 0
    }

    let status_when_disconnected = {
      rec_status: wait_text,
      device_name: "",
      detector_time: "",
      location_status: ""
    }
    updateStatus(status_when_disconnected)

    setTimeout(function () { startWebsocket(ws_url) }, 5000);
  };
};
