#include "../inc/main.h"

void run_status_thread(t_statusThreadData *status_data)
{
	t_data *data = status_data->data;
	
	while (data->program_running)
	{
		for (int i = 0; i < 3; i++)
		{
			t_scannerInfo *scanner = &status_data->scanner[i];
			json_object *json = set_API_sendData_readerStatus(scanner, "ONLINE");
			Post_JSON_to_API(json, API_URL_READER_STATUS, false);
		}

		sleep(API_STATUS_SEND_INTERVAL);
	}
}

int	safe_thread_printf(t_data *data, const char *format, ...)
{
	va_list args;
	int ret;

	pthread_mutex_lock(&data->print_mutex);
	va_start(args, format);
	ret = vprintf(format, args);
	va_end(args);
	pthread_mutex_unlock(&data->print_mutex);
	return ret;
}

int safe_thread_perrror(t_data *data, const char *message)
{
	int errnum = errno;
	pthread_mutex_lock(&data->print_mutex);
	perror(message);
	pthread_mutex_unlock(&data->print_mutex);
	errno = errnum;
	return -1;
}


int get_uptime_seconds(t_data *data)
{
	struct timeval tv;
	gettimeofday(&tv, NULL);

	return (int)(tv.tv_sec - data->uptime_seconds_start);
}

int current_time_iso8601(char *result) {
    char buffer[TIMESTAMP_SIZE];
    char tz[8];
    struct timeval tv;
    struct tm tm_info;

    gettimeofday(&tv, NULL);
    localtime_r(&tv.tv_sec, &tm_info);

    strftime(buffer, sizeof(buffer), "%Y-%m-%dT%H:%M:%S", &tm_info);
    snprintf(buffer + strlen(buffer), sizeof(buffer) - strlen(buffer), \
		".%03ld", tv.tv_usec / 1000);

    strftime(tz, sizeof(tz), "%z", &tm_info);
    snprintf(buffer + strlen(buffer), sizeof(buffer) - strlen(buffer), \
		"%c%c%c:%c%c", tz[0], tz[1], tz[2], tz[3], tz[4]);

	memcpy(result, buffer, TIMESTAMP_SIZE);
    return 0;
}

