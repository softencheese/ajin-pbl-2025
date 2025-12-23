#include "../inc/main.h"

int init_barcode_scanner()
{
	char device[] = "/dev/ttyACM0";
	int serial_port;

	serial_port = open(device, O_RDONLY);
	if (serial_port == -1) {
		perror("Error opening serial port");
		return -1;
	}
	
	tcflush(serial_port, TCIOFLUSH);
	return serial_port;
}

void loop_barcode_scan(t_data *data)
{
	char buffer[BUFFER_SIZE];
	int read_len = 0;

	while (1) {
		if ( (read_len = read(data->barcode_scanner, buffer, BUFFER_SIZE)) != -1)
			safe_thread_printf(data, "Scanned Barcode: %s", buffer);
		else
		{
			safe_thread_perrror(data, "Error reading from barcode scanner");
			break;
		}

		if (!data->program_running)
			return;
		usleep(1000);
	}
}

void close_barcode_scanner(int serial_port)
{
	if (serial_port != -1)
		close(serial_port);
}