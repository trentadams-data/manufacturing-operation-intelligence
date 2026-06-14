# Data Dictionary

## production_runs

| Column | Description |
| --- | --- |
| run_id | Unique identifier for each production run record. |
| date | Production date for the run. |
| plant | Plant location associated with the run. |
| production_line | Line or cell producing the item. |
| machine_id | Specific machine used for the run. |
| product_id | Product code linked to the product catalog. |
| shift | Shift in which the run occurred. |
| planned_minutes | Planned operating time in minutes. |
| operating_minutes | Actual minutes the line operated. |
| ideal_cycle_time_seconds | Standard cycle time per unit. |
| planned_units | Expected units based on planned time and cycle rate. |
| actual_units | Units produced during the run. |
| good_units | Units meeting quality standards. |
| scrap_units | Units discarded as scrap. |
| rework_units | Units sent for rework. |
| operator_team | Team responsible for the shift. |

## machine_events

| Column | Description |
| --- | --- |
| event_id | Unique identifier for a downtime or event record. |
| date | Date of the event. |
| production_line | Affected line. |
| machine_id | Affected machine. |
| shift | Shift when the event occurred. |
| event_type | Planned or unplanned event classification. |
| downtime_reason | Root reason such as sensor drift or bearing fault. |
| downtime_minutes | Lost time attributed to the event. |
| severity | Low, Medium, or High severity level. |

## maintenance_logs

| Column | Description |
| --- | --- |
| maintenance_id | Unique maintenance record identifier. |
| date | Date of maintenance activity. |
| machine_id | Machine receiving maintenance. |
| maintenance_type | Preventive, corrective, inspection, or replacement. |
| maintenance_minutes | Time spent on maintenance. |
| component | Component inspected or replaced. |
| issue_found | Observed issue or reason for intervention. |
| cost | Estimated maintenance cost. |

## quality_inspections

| Column | Description |
| --- | --- |
| inspection_id | Unique inspection record identifier. |
| date | Inspection date. |
| production_line | Line associated with the inspection. |
| machine_id | Machine related to the inspection. |
| product_id | Product under inspection. |
| shift | Shift during which the sample was collected. |
| sample_size | Number of units inspected. |
| defect_count | Count of defective units found. |
| defect_type | Classification of the defect detected. |
| measurement_value | Measured value for the sample. |
| target_value | Intended process target for the measurement. |
| lower_spec_limit | Lower allowed specification limit. |
| upper_spec_limit | Upper allowed specification limit. |

## sensor_readings

| Column | Description |
| --- | --- |
| reading_id | Unique sensor reading identifier. |
| timestamp | Time of the reading. |
| machine_id | Machine producing the reading. |
| temperature_c | Temperature in degrees Celsius. |
| vibration_mm_s | Vibration in millimeters per second. |
| pressure_bar | Pressure in bar. |
| runtime_hours | Cumulative operating hours. |
| alarm_count | Number of alarms raised at that reading. |

## products

| Column | Description |
| --- | --- |
| product_id | Product identifier. |
| product_name | Human-readable product name. |
| product_family | Product family or product group. |
| standard_cycle_time_seconds | Standard cycle time for the item. |
| unit_margin | Unit profit contribution used for economics. |

## work_centers

| Column | Description |
| --- | --- |
| machine_id | Machine identifier. |
| plant | Plant where the machine is located. |
| production_line | Line assigned to the machine. |
| machine_type | Machine class such as press or CNC. |
| install_year | Year the machine was installed. |
| criticality | Criticality ranking for reliability planning. |
