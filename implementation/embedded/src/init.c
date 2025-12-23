#include "../inc/main.h"

extern t_scannerInfo *g_reg_nfc_data;
extern t_scannerInfo *g_gen_nfc_data;

void init_data(t_data *data)
{
	data->program_running = 1;
	
	// if ( (data->barcode_scanner = init_barcode_scanner()) == -1)
	// {
	// 	perror("Failed to initialize barcode scanner\n");
	// 	exit(-1);
	// }
	if (pthread_mutex_init(&data->print_mutex, NULL) != 0)
	{
		perror("Failed to initialize print_mutex\n");
		close_barcode_scanner(data->barcode_scanner);
		exit(-1);
	}
	if (pthread_mutex_init(&data->usb_mutex, NULL) != 0)
	{
		perror("Failed to initialize usb_mutex\n");
		pthread_mutex_destroy(&data->print_mutex);
		close_barcode_scanner(data->barcode_scanner);
		exit(-1);
	}
	init_uptime(data);
}

void init_scannerInfo(t_scannerInfo *scanner, int device_num, char *port_name, t_data *data)
{
	json_object *json;

	scanner->device_num = device_num;
	memcpy(scanner->port_name, port_name, sizeof(scanner->port_name));
	memcpy(scanner->last_scan_time, NONE_TIMESTAMP, TIMESTAMP_SIZE);
	scanner->total_scans = 0;
	scanner->error_count = 0;
	scanner->data = data;
	if ( (scanner->NFCReader_hdev = usbRFIDreader_init(device_num)) == -1 )
	{
		perror("Failed to initialize USB RFID reader\n");
		exit(-1);
	}

	json = set_API_sendData_readerStatus(scanner, "ONLINE");
	Post_JSON_to_API(json, API_URL_READER_STATUS, true);
	printf("Initialized scanner on port %s (hdev %d)\n", scanner->port_name, scanner->NFCReader_hdev);
}


void init_uptime(t_data *data)
{
	struct timeval tv;
	gettimeofday(&tv, NULL);

	data->uptime_seconds_start = tv.tv_sec;
}

void init_status_thread_data(t_statusThreadData *status_data, t_scannerInfo *reg_nfc, t_scannerInfo *gen_nfc, t_data *data)
{
	status_data->scanner[0] = *reg_nfc;
	status_data->scanner[1] = *gen_nfc;
	status_data->data = data;
}

void setup(t_data *data, t_scannerInfo *reg_nfc, t_scannerInfo *gen_nfc, t_statusThreadData *status_data)
{
	signal(SIGINT, signal_handler);
	signal(SIGTERM, signal_handler);

	init_data(data);
	init_scannerInfo(reg_nfc, SCANNER_TYPE_REGISTER, "COM00_REG", data);
	init_scannerInfo(gen_nfc, SCANNER_TYPE_GENERIC, "COM00_GEN", data);
	init_status_thread_data(status_data, reg_nfc, gen_nfc, data);

	g_reg_nfc_data = reg_nfc;
	g_gen_nfc_data = gen_nfc;
}