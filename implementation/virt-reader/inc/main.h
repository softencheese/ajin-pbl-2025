

#ifndef MAIN_H
# define MAIN_H

# include <stdio.h>
# include <stdlib.h>
# include <unistd.h>
# include <stdbool.h>
# include <string.h>
# include <ctype.h>
# include <termios.h>
# include <pthread.h>
# include <stdarg.h>
# include <signal.h>
# include <errno.h>
# include <fcntl.h>
# include <sys/time.h>

# include <readline/readline.h>
# include <readline/history.h>

# include <curl/curl.h>

# include <json-c/json.h>

# ifndef COM_PORT_BASE_NAME
#  define COM_PORT_BASE_NAME		"COM00"
# endif

# define STATION_NUM 				1

# define NFC_SERIAL_LEN_MAX			17

# define SCANNER_TYPE_REGISTER		0
# define SCANNER_TYPE_INPUT		    1
# define SCANNER_TYPE_OUTPUT		2

# define PORT_NAME_SIZE				32
# define TIMESTAMP_SIZE				30
# define NONE_TIMESTAMP				"9999-01-01T00:00:00.000+00:00"

# define API_URL_READER_STATUS		"http://localhost:8000/api/v1/rfid/reader-status"
# define API_URL_SCAN_DATA			"http://localhost:8000/api/v1/rfid/scan"
# define API_URL_READER_LOCATIONS   "http://localhost:8000/api/v1/reader-locations"

# define API_URL_PROCESS_LOTS(id)       "http://localhost:8000/api/v1/processes/" id "/alive-lots"
# define API_STATUS_SEND_INTERVAL	10 // seconds

typedef struct s_data
{
    
	int					program_running;
	int					uptime_seconds_start;
    int                 process_id;
	pthread_mutex_t		print_mutex;
}	t_data;

typedef struct s_ResponseData {
    char	*data;
    size_t	size;
} ResponseData;

typedef struct s_scannerInfo
{
    int     type;
	int		device_type;
	char	port_name[PORT_NAME_SIZE];
	char	last_scan_time[TIMESTAMP_SIZE];
	int		total_scans;
	int		error_count;
	t_data	*data;
}	t_scannerInfo;

typedef struct s_statusThreadData
{
	t_scannerInfo	scanner[3];
	t_data			*data;
}	t_statusThreadData;

void	signal_handler(int sig);

// readline.c
void run_input_loop(t_data *data);
void print_usage(void);

// virt.c
int		process_card_input(const char *input_buffer, char *snr_str_out, t_scannerInfo *scanner);

// API.c
int get_JSON_from_API(const char *url, json_object **json);
json_object *set_API_sendData_readerStatus(t_scannerInfo *scanner, const char *status);
json_object *set_API_sendData_scan(const char *epc, t_scannerInfo *scanner);
int		Post_JSON_to_API(json_object *json, const char *url, int is_response_print);
int		Put_JSON_to_API(json_object *json, const char *url, int is_response_print);

// data_control.c
int manager_process_lots_command(t_data *data, const char *command_args);

// int     get_lot_id_for_pallet(json_object *json, const char *target_epc);
// int     get_item_id_for_pallet(json_object *json, const char *target_epc);
// void    get_lotList_for_item_id(int item_id);


// init.c
void	init_data(t_data *data);
void	init_scannerInfo(t_scannerInfo *scanner, int device_type, char *port_name, t_data *data);
void	init_uptime(t_data *data);
void	init_status_thread_data(t_statusThreadData *status_data, t_scannerInfo *reg_nfc, t_scannerInfo *in_nfc, t_scannerInfo *out_nfc, t_data *data);
void	set_process_id(t_data *data);
void	setup(t_data *data, t_scannerInfo *in_nfc, t_scannerInfo *out_nfc, t_scannerInfo *reg_nfc, t_statusThreadData *status_data);

// utils.c
void	run_status_thread(t_statusThreadData *status_data);
int		get_uptime_seconds(t_data *data);
int		current_time_iso8601(char *result);
size_t	WriteMemoryCallback(void *data, size_t size, size_t nmemb, void *userp);

#endif /* MAIN_H */
