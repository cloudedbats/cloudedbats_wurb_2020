
// Generic functions.
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

// For detector mode.
function modeSelectOnChange(update_detector) {
  let selected_value = detector_mode_select_id.options[detector_mode_select_id.selectedIndex].value
  hideDivision(div_manual_triggering_id);
  hideDivision(div_detector_power_off_id);
  if (selected_value == "mode-off") {
    // stopRecording()
    if (update_detector) {
      saveSettings()
    }
  }
  else if (selected_value == "mode-on") {
    if (update_detector) {
      saveSettings()
    }
    // startRecording()
  }
  else if (selected_value == "mode-auto") {
    if (update_detector) {
      saveSettings()
    }
    // startRecording()
  }
  else if (selected_value == "mode-manual") {
    showDivision(div_manual_triggering_id);
    if (update_detector) {
      saveSettings()
    }
    // startRecording()
  }
  else if (selected_value == "mode-scheduler-on") {
    // stopRecording()
    if (update_detector) {
      saveSettings()
    }
  }
  else if (selected_value == "mode-scheduler-auto") {
    // stopRecording()
    if (update_detector) {
      saveSettings()
    }
  }
  else if (selected_value == "load-user-default") {
    stopRecording()
    loadSettings(settings_type="user-default")
  }
  else if (selected_value == "load-start-up") {
    stopRecording()
    loadSettings(settings_type="start-up")
  }
  else if (selected_value == "load-factory-default") {
    stopRecording()
    loadSettings(settings_type="factory-default")
  }
  else if (selected_value == "detector-power-off") {
    showDivision(div_detector_power_off_id);
  }
  // Trigging Audio feedback sliders
  feedback_volume_slider_id.oninput()
  feedback_pitch_slider_id.oninput()
}

// For the geographic location tile.
function geoLocationSourceOnChange(update_detector) {
  let selected_value = location_source_select_id.options[location_source_select_id.selectedIndex].value
  location_button_text_id.innerHTML = "Save"
  if (selected_value == "geo-not-used") {
    latitude_dd_id.value = "0.0";
    longitude_dd_id.value = "0.0";
    latitude_dd_id.disabled = true;
    longitude_dd_id.disabled = true;
    location_button_id.disabled = true;
    if (update_detector) {
      saveLocationSource()
    }
  }
  else if (selected_value == "geo-manual") {
    getManualLocation();
    location_button_text_id.innerHTML = "Save lat/long"
    latitude_dd_id.disabled = false;
    longitude_dd_id.disabled = false;
    location_button_id.disabled = false;
    if (update_detector) {
      saveLocationSource()
    }
  }
  // Disabled, HTTPS is needed.
  // else if (selected_value == "geo-client-gps") {
  //   activateGeoLocation()
  //   latitude_dd_id.disabled = true;
  //   longitude_dd_id.disabled = true;
  //   location_button_id.disabled = false;
  //   if (update_detector) {
  //     saveLocationSource()
  //   }
  // }
  else if (selected_value == "geo-gps") {
    location_button_text_id.innerHTML = "Use as manually entered"
    latitude_dd_id.disabled = true;
    longitude_dd_id.disabled = true;
    location_button_id.disabled = false;
    if (update_detector) {
      saveLocationSource()
    }
  }
  else if (selected_value == "geo-gps-or-manual") {
    location_button_text_id.innerHTML = "Save"
    latitude_dd_id.disabled = true;
    latitude_dd_id.disabled = true;
    longitude_dd_id.disabled = true;
    location_button_id.disabled = true;
    if (update_detector) {
      saveLocationSource()
    }
  }
  else if (selected_value == "geo-last-gps-or-manual") {
    location_button_text_id.innerHTML = "Save"
    latitude_dd_id.disabled = true;
    longitude_dd_id.disabled = true;
    location_button_id.disabled = true;
    if (update_detector) {
      saveLocationSource()
    }
  }
  else {
    latitude_dd_id.disabled = true;
    longitude_dd_id.disabled = true;
    location_button_id.disabled = true;
  }
}

// Disabled, HTTPS is needed.
// function activateGeoLocation() {
//   if (navigator.geolocation) {
//     navigator.geolocation.getCurrentPosition(showPosition, errorCallback, { timeout: 10000 });
//     // navigator.geolocation.getCurrentPosition(showLocation);
//     // navigator.geolocation.watchPosition(showLocation);
//     // navigator.geolocation.clearWatch(showLocation);
//   } else {
//     alert(`Geo location from client:\nNot supported by this browser.`);
//   };
// };
// function showPosition(location) {
//   latitude_id.value = location.coords.latitude;
//   longitude_id.value = location.coords.longitude;
// };
// function errorCallback(error) {
//   alert(`Geo location from client:\nERROR(${error.code}): ${error.message}`);
// };

function audioFeedbackSliders() {
  // Update slider values.
  feedback_volume_id.innerHTML = "[" + feedback_volume_slider_id.value + "%]";
  feedback_pitch_id.innerHTML = "[1/" + feedback_pitch_slider_id.value + "]";
  // On changes.
  feedback_volume_slider_id.oninput = function () {
    feedback_volume_id.innerHTML = "[" + this.value + "%]";
  }
  feedback_volume_slider_id.onchange = function () {
    // Send to server.
    feedback_volume_id.innerHTML = "[" + this.value + "%]";
    setAudioFeedback()
  }
  feedback_pitch_slider_id.oninput = function () {
    feedback_pitch_id.innerHTML = "[1/" + this.value + "]";
  }
  feedback_pitch_slider_id.onchange = function () {
    // Send to server.
    feedback_pitch_id.innerHTML = "[1/" + this.value + "]";
    setAudioFeedback()
  }
}

// Used for the main tabs in the settings tile.
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
// Functions used to updates fields based on response contents.
function updateStatus(status) {
  detector_status_id.innerHTML = status.rec_status;
  if (status.device_name != "") {
    detector_status_id.innerHTML += "<br>"
    detector_status_id.innerHTML += status.device_name;
  }
  detector_time_id.innerHTML = status.detector_time;
  location_status_id.innerHTML = status.location_status;
}

function updateLocation(location) {
  location_source_select_id.value = location.geo_source
  if (location.geo_source == "geo-manual") {
    latitude_dd_id.value = location.manual_latitude_dd
    longitude_dd_id.value = location.manual_longitude_dd
  } else {
    latitude_dd_id.value = location.latitude_dd
    longitude_dd_id.value = location.longitude_dd
  }
  // Check geolocation:
  geoLocationSourceOnChange(update_detector = false);
}

function updateLatLong(latlong) {
  latitude_dd_id.value = latlong.latitude_dd
  longitude_dd_id.value = latlong.longitude_dd
}

function updateSettings(settings) {

  last_used_settings = settings

  detector_mode_select_id.value = settings.rec_mode
  settings_file_directory_id.value = settings.file_directory
  settings_file_directory_date_option_id.value = settings.file_directory_date_option
  settings_filename_prefix_id.value = settings.filename_prefix
  settings_detection_limit_id.value = settings.detection_limit_khz
  settings_detection_sensitivity_id.value = settings.detection_sensitivity_dbfs
  settings_detection_algorithm_id.value = settings.detection_algorithm
  settings_rec_length_id.value = settings.rec_length_s
  settings_rec_type_id.value = settings.rec_type
  settings_feedback_on_off_id.value = settings.feedback_on_off
  feedback_volume_slider_id.value = settings.feedback_volume
  feedback_pitch_slider_id.value = settings.feedback_pitch
  settings_feedback_filter_low_id.value = settings.feedback_filter_low_khz
  settings_feedback_filter_high_id.value = settings.feedback_filter_high_khz
  settings_startup_option_id.value = settings.startup_option
  settings_scheduler_start_event_id.value = settings.scheduler_start_event
  settings_scheduler_start_adjust_id.value = settings.scheduler_start_adjust
  settings_scheduler_stop_event_id.value = settings.scheduler_stop_event
  settings_scheduler_stop_adjust_id.value = settings.scheduler_stop_adjust
  settings_scheduler_post_action_id.value = settings.scheduler_post_action
  settings_scheduler_post_action_delay_id.value = settings.scheduler_post_action_delay

  modeSelectOnChange(update_detector=false)

  // Trigging Audio feedback sliders
  feedback_volume_slider_id.oninput()
  feedback_pitch_slider_id.oninput()
}

function saveUserDefaultSettings() {
  saveSettings(settings_type="user-defined")
}

function saveStartupSettings() {
  saveSettings(settings_type="startup")
}

function updateLogTable(log_rows) {
  html_table_rows = ""
  for (row_index in log_rows) {
    html_table_rows += "<tr><td>"
    html_table_rows += log_rows[row_index]
    html_table_rows += "</tr></td>"
  }
  document.getElementById("detector_log_table_id").innerHTML = html_table_rows
}
