
function define_global_variables() {

  // Detector unit tile.
  const detector_mode_select_id = document.getElementById("detector_mode_select_id");
  const div_manual_triggering_id = document.getElementById("div_manual_triggering_id");
  const div_detector_power_off_id = document.getElementById("div_detector_power_off_id");
  const detector_status_id = document.getElementById("detector_status_id");
  const detector_time_id = document.getElementById("detector_time_id");
  const detector_log_table_id = document.getElementById("detector_log_table_id");

  // Geographic location tile.
  const location_source_select_id = document.getElementById("location_source_select_id");
  const location_status_id = document.getElementById("location_status_id");
  const latitude_dd_id = document.getElementById("latitude_dd_id");
  const longitude_dd_id = document.getElementById("longitude_dd_id");
  const location_button_id = document.getElementById("location_button_id");
  const location_button_text_id = document.getElementById("location_button_text_id");

  // Settings tile. Tab hide/show.
  const tab_settings_basic_id = document.getElementById("tab_settings_basic_id");
  const tab_settings_more_id = document.getElementById("tab_settings_more_id");
  const tab_settings_scheduler_id = document.getElementById("tab_settings_scheduler_id");
  const div_settings_basic_id = document.getElementById("div_settings_basic_id");
  const div_settings_more_id = document.getElementById("div_settings_more_id");
  const div_settings_scheduler_id = document.getElementById("div_settings_scheduler_id");

  // Fields and buttons.
  const settings_file_directory_id = document.getElementById("settings_file_directory_id");
  const settings_file_directory_date_option_id = document.getElementById("settings_file_directory_date_option_id");
  const settings_filename_prefix_id = document.getElementById("settings_filename_prefix_id");
  const settings_detection_limit_id = document.getElementById("settings_detection_limit_id");
  const settings_detection_sensitivity_id = document.getElementById("settings_detection_sensitivity_id");
  const settings_detection_algorithm_id = document.getElementById("settings_detection_algorithm_id");
  const settings_rec_length_id = document.getElementById("settings_rec_length_id");
  const settings_rec_type_id = document.getElementById("settings_rec_type_id");
  const settings_feedback_on_off_id = document.getElementById("settings_feedback_on_off_id");
  const settings_feedback_filter_low_id = document.getElementById("settings_feedback_filter_low_id");
  const settings_feedback_filter_high_id = document.getElementById("settings_feedback_filter_high_id");
  const settings_startup_option_id = document.getElementById("settings_startup_option_id");

  const settings_scheduler_start_event_id = document.getElementById("settings_scheduler_start_event_id");
  const settings_scheduler_start_adjust_id = document.getElementById("settings_scheduler_start_adjust_id");
  const settings_scheduler_stop_event_id = document.getElementById("settings_scheduler_stop_event_id");
  const settings_scheduler_stop_adjust_id = document.getElementById("settings_scheduler_stop_adjust_id");
  const settings_scheduler_post_action_id = document.getElementById("settings_scheduler_post_action_id");
  const settings_scheduler_post_action_delay_id = document.getElementById("settings_scheduler_post_action_delay_id");
  const settings_save_button_id = document.getElementById("settings_save_button_id");
  const settings_reset_button_id = document.getElementById("settings_reset_button_id");
  const settings_default_button_id = document.getElementById("settings_default_button_id");

  // Audio feedback sliders.
  const feedback_volume_slider_id = document.getElementById("feedback_volume_slider_id");
  const feedback_volume_id = document.getElementById("feedback_volume_id");
  const feedback_pitch_slider_id = document.getElementById("feedback_pitch_slider_id");
  const feedback_pitch_id = document.getElementById("feedback_pitch_id");

  // Used to save last used settings.
  var last_used_settings;
};
