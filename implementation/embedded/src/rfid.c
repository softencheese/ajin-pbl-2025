#include "../inc/main.h"

int usbRFIDreader_init(int device_num)
{
	char            device_path[64];
	unsigned char   szVer[128];
	int             hdev;
	int			 	try_count = 0;

	while(try_count < 5)
	{
		sprintf(device_path, "/dev/usb/hiddev%d", device_num);
		if( (hdev = lc_init_ex(2, device_path, BAUDRATE)) == -1 )
		{
			printf("Try to open %s\n", device_path);
			printf("lc_init_ex ERR %d\n", hdev);
			return -1;
		}

		if (lc_getver(hdev, szVer) == 0)
		{
			printf("version: %s\n", szVer);
			break;
		}  
		printf("%s init error\ttry count : %d (Max try 5)", device_path, try_count + 1);
	} 
	if (try_count == 5)
		return -1;
	return hdev;
}

int print_card_info(t_data *data, unsigned char *snr, unsigned char snSize, unsigned char sak, unsigned int tag)
{
	pthread_mutex_lock(&data->print_mutex);
	printf("Card detected: SNR=");
	for (int i = 0; i < snSize; i++)
		printf("%02X ", snr[i]);
	printf(", SAK=%02X, TAG=%08X\n", sak, tag);
	pthread_mutex_unlock(&data->print_mutex);
	return 0;
}

int post_card_info(t_scannerInfo *scanner, unsigned char *snr, unsigned char snSize)
{
	char snr_str[NFC_SERIAL_LEN_MAX * 2 + 1];
	json_object *json;
	
	for (int i = 0; i < snSize; i++)
		sprintf(&snr_str[i * 2], "%02X", snr[i]);
	snr_str[snSize * 2] = '\0';
	json = set_API_sendData_scan(snr_str, scanner);

	Post_JSON_to_API(json, API_URL_SCAN_DATA, true);	
	return 0;
}

// 카드를 감지하는 함수
int detectCards(t_scannerInfo *data)
{
    unsigned char   prevSNR[NFC_SERIAL_LEN_MAX];
    unsigned char   snr[NFC_SERIAL_LEN_MAX];
    unsigned char   snSize;
    unsigned char   sak;
    unsigned int    tag;
    int             cardResult;

    bool noCardmsg = true;
    memset(prevSNR, 0, NFC_SERIAL_LEN_MAX);
    memset(snr, 0, NFC_SERIAL_LEN_MAX);
    
	while (1)
    {
		pthread_mutex_lock(&data->data->usb_mutex);
		
		lc_rfReset(data->NFCReader_hdev, 5);
		
        cardResult = lc_card(data->NFCReader_hdev, 1, snr, &snSize, &tag, &sak);
		pthread_mutex_unlock(&data->data->usb_mutex);
		
		if (cardResult)
        {
			if (noCardmsg)
			{
				memset(prevSNR, 0, NFC_SERIAL_LEN_MAX);
				safe_thread_printf(data->data, "[%s] No card detected\n", data->port_name);
				noCardmsg = false;
			}
        }
        else if (strncmp((const char*)snr, (const char*)prevSNR, snSize) != 0)
        {
            memcpy(prevSNR, snr, snSize);
            noCardmsg = true;
			current_time_iso8601(data->last_scan_time);
			data->total_scans += 1;
			print_card_info(data->data, snr, snSize, sak, tag);
			post_card_info(data, snr, snSize);
        }
		usleep(30000);
		if (!data->data->program_running)
			break;
    }
    return 0;
}

// LED 테스트 함수
void test_led(int hdev)
{
    lc_led(hdev, NFC_LED1, NFC_LED_OFF);
    lc_led(hdev, NFC_LED2, NFC_LED_ON);
    sleep(1);
    lc_led(hdev, NFC_LED2, NFC_LED_OFF);
    lc_led(hdev, NFC_LED1, NFC_LED_ON);
    sleep(1);
}