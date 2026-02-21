#include "../inc/main.h"

static void remove_spaces(const char *src, char *dst)
{
	while (*src)
	{
		if (*src != ' ')
			*dst++ = *src;
		++src;
	}
	*dst = '\0';
}

static bool hex_string_to_bytes(const char *hex_str, unsigned char *bytes, int *out_size)
{
	int len = strlen(hex_str);
	
	if (len % 2 != 0 || len == 0)
	{
		printf("Invalid input: must be hex digits (even number of characters)\n");
		return false;
	}
	
	int byte_count = len / 2;
	if (byte_count > NFC_SERIAL_LEN_MAX)
	{
		printf("Input too long (max %d bytes)\n", NFC_SERIAL_LEN_MAX);
		return false;
	}
	
	for (int i = 0; i < byte_count; i++)
	{
		char hex_byte[3] = {hex_str[i*2], hex_str[i*2+1], '\0'};
		char *endptr;
		long val = strtol(hex_byte, &endptr, 16);
		if (*endptr != '\0')
		{
			printf("Invalid hex character in input\n");
			return false;
		}
		bytes[i] = (unsigned char)val;
	}
	
	*out_size = byte_count;
	return true;
}

static int send_card_to_server(const char *card_id, t_scannerInfo *scanner)
{
	printf("[%s] Card ID: %s\n", scanner->port_name, card_id);
	
	json_object *json = set_API_sendData_scan(card_id, scanner);
	int result = Post_JSON_to_API(json, API_URL_SCAN_DATA, true);
	
	if (result != 0) {
		scanner->error_count += 1;
	}
	
	return result;
}

int process_card_input(const char *input_buffer, char *snr_str_out, t_scannerInfo *scanner)
{
	char snr_str[NFC_SERIAL_LEN_MAX * 2 + 1];
	unsigned char snr[NFC_SERIAL_LEN_MAX];

	int snSize;

	remove_spaces(input_buffer, snr_str);
	
	if (!hex_string_to_bytes(snr_str, snr, &snSize))
		return -1;
	
	current_time_iso8601(scanner->last_scan_time);
	scanner->total_scans += 1;
	
	for (int i = 0; i < snSize; i++)
		sprintf(&snr_str[i * 2], "%02X", snr[i]);
	snr_str[snSize * 2] = '\0';
	
	if (snr_str_out != NULL)
		strcpy(snr_str_out, snr_str);
    
    if (send_card_to_server(snr_str, scanner) != 0) {
		fprintf(stderr, "Failed to send card data to server for EPC: %s\n", snr_str);
		return -1;
	}

    return 0;
}
