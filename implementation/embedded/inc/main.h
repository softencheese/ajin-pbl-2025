

#ifndef MAIN_H
# define MAIN_H

# include <stdio.h>
# include <stdlib.h>
# include <unistd.h>
# include <stdbool.h>
# include <string.h>
# include <termios.h>
# include <pthread.h>
# include <stdarg.h>
# include <signal.h>
# include <errno.h>
# include <fcntl.h>
# include <sys/time.h>

# include <curl/curl.h>

# include "nfc/comPro.h"
# include "json/json.h"

# define STATION_NUM 				1

# define BAUDRATE					115200
# define BUFFER_SIZE				2024
# define NFC_SERIAL_LEN_MAX			17

# define NFC_LED1					1
# define NFC_LED2					2
# define NFC_LED_ON					1
# define NFC_LED_OFF				0

# define SCANNER_TYPE_REGISTER		0
# define SCANNER_TYPE_GENERIC		1

# define PORT_NAME_SIZE				10
# define TIMESTAMP_SIZE				30
# define NONE_TIMESTAMP				"9999-01-01T00:00:00.000+00:00"

# define API_URL_READER_STATUS		"http://10.143.2.7:8000/api/v1/rfid/reader-status"
# define API_URL_SCAN_DATA			"http://10.143.2.7:8000/api/v1/rfid/scan"
# define API_STATUS_SEND_INTERVAL	10 // seconds

typedef struct s_data
{
	int					barcode_scanner;
	int					program_running;
	int					uptime_seconds_start;
	pthread_mutex_t		print_mutex;
	pthread_mutex_t		usb_mutex;
}	t_data;

typedef struct s_ResponseData {
    char	*data;
    size_t	size;
} ResponseData;

typedef struct s_scannerInfo
{
	int		device_num;
	int		NFCReader_hdev;
	char	port_name[PORT_NAME_SIZE];
	char	last_scan_time[TIMESTAMP_SIZE];
	int		total_scans;
	int		error_count;
	t_data	*data;
}	t_scannerInfo;

typedef struct s_statusThreadData
{
	t_scannerInfo	scanner[2];
	t_data			*data;
}	t_statusThreadData;

void	signal_handler(int sig);

// rfid.c
int		usbRFIDreader_init(int device_num);
int		print_card_info(t_data *data, unsigned char *snr, unsigned char snSize, unsigned char sak, unsigned int tag);
int		post_card_info(t_scannerInfo *scanner, unsigned char *snr, unsigned char snSize);
int		detectCards(t_scannerInfo *data);
void	test_led(int hdev);

// barcode.c
int		init_barcode_scanner();
void	loop_barcode_scan(t_data *data);
void	close_barcode_scanner(int serial_port);

// init.c
void	init_data(t_data *data);
void	init_scannerInfo(t_scannerInfo *scanner, int device_num, char *port_name, t_data *data);
void	init_uptime(t_data *data);
void	init_status_thread_data(t_statusThreadData *status_data, t_scannerInfo *reg_nfc, t_scannerInfo *gen_nfc, t_data *data);
void	setup(t_data *data, t_scannerInfo *reg_nfc, t_scannerInfo *gen_nfc, t_statusThreadData *status_data);

// utils.c
void	run_status_thread(t_statusThreadData *status_data);
int		safe_thread_printf(t_data *data, const char *format, ...);
int		safe_thread_perrror(t_data *data, const char *message);
int		get_uptime_seconds(t_data *data);
int		current_time_iso8601(char *result);

// API.c
size_t		WriteMemoryCallback(void *data, size_t size, size_t nmemb, void *userp);
int			Post_JSON_to_API(json_object *json, const char *url, int is_response_print);
json_object	*set_API_sendData_readerStatus(t_scannerInfo *scanner, const char *status);
json_object	*set_API_sendData_scan(char *epc, t_scannerInfo *scanner);

#endif /* MAIN_H */
