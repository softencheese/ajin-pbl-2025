#include "../inc/main.h"

extern t_scannerInfo *g_in_nfc_data;
extern t_scannerInfo *g_out_nfc_data;
extern t_scannerInfo *g_reg_nfc_data;

void init_data(t_data *data)
{
	data->program_running = 1;
	
	if (pthread_mutex_init(&data->print_mutex, NULL) != 0)
	{
		perror("Failed to initialize print_mutex\n");
		exit(-1);
	}
	init_uptime(data);
}

void init_scannerInfo(t_scannerInfo *scanner, int device_type, char *port_name, t_data *data)
{
	json_object *json;

	scanner->device_type = device_type;
	strncpy(scanner->port_name, port_name, PORT_NAME_SIZE - 1);
	scanner->port_name[PORT_NAME_SIZE - 1] = '\0';
	memcpy(scanner->last_scan_time, NONE_TIMESTAMP, TIMESTAMP_SIZE);
	scanner->total_scans = 0;
	scanner->error_count = 0;
	scanner->data = data;

	json = set_API_sendData_readerStatus(scanner, "ONLINE");
	Post_JSON_to_API(json, API_URL_READER_STATUS, true);
	printf("Initialized scanner on port %s (Terminal Input Mode)\n", scanner->port_name);
}


void init_uptime(t_data *data)
{
	struct timeval tv;
	gettimeofday(&tv, NULL);

	data->uptime_seconds_start = tv.tv_sec;
}

void set_process_id(t_data *data)
{
    json_object *json = NULL;
    json_object *items = NULL;

    if (get_JSON_from_API(API_URL_READER_LOCATIONS, &json) != 0 || json == NULL)
    {
        fprintf(stderr, "Failed to get reader locations from API\n");
        data->process_id = 0;
        return;
    }

    items = json_object_object_get(json, "items");
    if (items == NULL || !json_object_is_type(items, json_type_array))
    {
        fprintf(stderr, "No items found in reader locations response\n");
        json_object_put(json);
        data->process_id = 0;
        return;
    }

    data->process_id = 0;
    for (size_t i = 0; i < json_object_array_length(items); i++)
    {
        json_object *item = json_object_array_get_idx(items, i);
        json_object *port_name_obj = json_object_object_get(item, "port_name");
        if (port_name_obj == NULL)
            continue;
        
        const char *port_name = json_object_get_string(port_name_obj);
        if (port_name && strncmp(port_name, COM_PORT_BASE_NAME, strlen(COM_PORT_BASE_NAME)) == 0)
        {
            json_object *process_id_obj = json_object_object_get(item, "process_id");
            if (process_id_obj)
                data->process_id = json_object_get_int(process_id_obj);
            printf("Set process ID to %d for port %s\n", data->process_id, port_name);
            break;
        }
    }
    json_object_put(json);
}

void init_status_thread_data(t_statusThreadData *status_data, t_scannerInfo *in_nfc, t_scannerInfo *out_nfc, t_scannerInfo *reg_nfc, t_data *data)
{
	status_data->scanner[0] = *in_nfc;
	status_data->scanner[1] = *out_nfc;
	status_data->scanner[2] = *reg_nfc;
	status_data->data = data;
}

void setup(t_data *data, t_scannerInfo *reg_nfc, t_scannerInfo *in_nfc, t_scannerInfo *out_nfc, t_statusThreadData *status_data)
{
	signal(SIGINT, signal_handler);
	signal(SIGTERM, signal_handler);

	init_data(data);
	init_scannerInfo(in_nfc, SCANNER_TYPE_INPUT, COM_PORT_BASE_NAME "-IN", data);
	init_scannerInfo(out_nfc, SCANNER_TYPE_OUTPUT, COM_PORT_BASE_NAME "-OUT", data);
	init_scannerInfo(reg_nfc, SCANNER_TYPE_REGISTER, COM_PORT_BASE_NAME "-REG", data);
	init_status_thread_data(status_data, in_nfc, out_nfc, reg_nfc, data);
    set_process_id(data);
	g_reg_nfc_data = reg_nfc;
	g_in_nfc_data = in_nfc;
	g_out_nfc_data = out_nfc;
}