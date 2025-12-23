
#ifndef __COMPRO_H__
#define __COMPRO_H__

#if defined(linux) || defined(__LYNX) || defined(__unix) || defined(_AIX)|| defined(__mips__)
#define _stdcall
#define __stdcall
#include <stdbool.h>
#define BOOL	bool
#endif

#ifdef __cplusplus
extern "C"
{
#endif

//===============================================
/*---------- Common Functions--------*/
//===============================================
int _stdcall lc_init(int port,long baud);
int _stdcall lc_init_ex(int type, char* path, long baud);
int _stdcall lc_exit(int icdev);
int _stdcall lc_chooseCommuniDevcieAddr(unsigned int devAddr);
//ASC to HEX
int  _stdcall asc_hex(unsigned char *strasc,unsigned char *strhex,int length);
//HEX to ASC
int  _stdcall hex_asc(unsigned char *strhex,unsigned char *strasc,int length);
int _stdcall lc_commonTransferInfo(unsigned char* pBuf_in, int* len_in, unsigned char* pBuf_out, int* len_out);
int _stdcall lc_getFlashUserMemSize(int icdev, unsigned int* pSize);
int _stdcall lc_getver(int icdev,unsigned char *buff);
int _stdcall lc_srd_flash(int icdev,int offset,int length,
								   unsigned char *rec_buffer);
int _stdcall lc_swr_flash(int icdev,int offset,int length,
								   unsigned char* buffer);
int _stdcall lc_devReboot(int icdev);
int _stdcall lc_setAddress(int icdev, unsigned int addr);
int _stdcall lc_getAddress(int icdev, unsigned int* pAddr);
int _stdcall lc_setBaudRate(int icdev,int baud);
int _stdcall lc_SetDevPassword(int icdev,unsigned char pwdAddr, unsigned char pwdLen, unsigned char *pPwd);
int _stdcall lc_crypt(int icdev,unsigned char fEn_De, unsigned char algorithm,
	unsigned int srcLen, unsigned char *pSrc_in, unsigned char* pIv_in,
	unsigned char* pDest_out, unsigned int* pDestLen_out);
int _stdcall lc_setReadOnlyPara(int icdev,unsigned char* pPara,int paraLen);
int _stdcall lc_getReadOnlyPara(int icdev, unsigned char* pPara_out, int* paraLen_out);
int _stdcall lc_setAppendData(int icdev, unsigned char* para_in, unsigned char paraLen);
int _stdcall lc_getAppendData(int icdev, unsigned char* pPara_out, unsigned char* pLen_out);
int _stdcall lc_getOutDataSequence(int icdev, unsigned char* pPara_out, unsigned char* pLen_out);
int _stdcall lc_setOutDataSequence(int icdev, unsigned char* para_in, unsigned char paraLen);
//0->Read/Write, 1->Read only
int _stdcall lc_setReaderMode(int icdev, unsigned char mode);
int _stdcall lc_getReaderMode(int icdev, unsigned char* mode);
int _stdcall lc_set_identifyResponsePara(int icdev, unsigned char* pParaIn, unsigned char paraLen);
int _stdcall lc_get_identifyResponsePara(int icdev, unsigned char* pParaOut, unsigned char* pParaLen);
int _stdcall lc_set_AutoReportDataType(int icdev, unsigned char type,unsigned short outputPort);
int _stdcall lc_get_AutoReportDataType(int icdev, unsigned char* type_out, unsigned short* pOutputPort);
int _stdcall lc_getAutoReturnedData(int icdev, unsigned char* pRData, unsigned int* pRLen);
//===============================================
/*---------- device Functions--------*/
//===============================================
int _stdcall lc_beep(int icdev,unsigned int _Msec);
int _stdcall lc_led(int icdev, int iLED, int on_off);

int _stdcall lc_getBTMAC(int icdev, unsigned char* pMAC);//MAC contain 6 bytes
int _stdcall lc_setBTName(int icdev, char* szName);
int _stdcall lc_getBTName(int icdev, char* pszName);
int _stdcall lc_getPower(int icdev, unsigned char* pPowerPercent);
int _stdcall lc_setShutdownTimer(int icdev, int time);
int _stdcall lc_shutDown(int icdev);

//// expend functions
int _stdcall lc_setTestState(int icdev, unsigned char newSt);

//===============================================
/*---------- NB  Functions--------*/
//===============================================
int _stdcall lc_setNB_serverIP(int icdev, unsigned char* pIP_in);
int _stdcall lc_getNB_serverIP(int icdev, unsigned char* pIP_out);
int _stdcall lc_setNB_serverPort(int icdev, int port);
int _stdcall lc_getNB_serverPort(int icdev, int* pPort);
int _stdcall lc_setNB_URL(int icdev, unsigned char* pURL_in);
int _stdcall lc_getNB_URL(int icdev, unsigned char* pURL_out);
int _stdcall lc_setNB_AutoReport(int icdev, unsigned char fEnable);
int _stdcall lc_getNB_AutoReport(int icdev, unsigned char* fEnable_out);
//===============================================
/*----------RFID  Functions--------*/
//===============================================
int _stdcall lc_setANT(int icdev, unsigned char status);
int _stdcall lc_selectANT(int icdev, unsigned int iANT);
int _stdcall lc_rfReset(int icdev, unsigned int time);
int _stdcall lc_card(int icdev,unsigned char _Mode,unsigned char *_Snr, unsigned char* _outSnrSize, unsigned int* pTag, unsigned char* pSak);
int _stdcall lc_requestAndIdentifyTypeA(int icdev,unsigned char _Mode,unsigned char *_Snr, unsigned char* _outSnrSize, 
	unsigned char* pfTagType, unsigned char* pfCompliant14443_4);
int _stdcall lc_authentication(int icdev, unsigned char _Mode, unsigned char sector,unsigned char* pKey);
int _stdcall lc_read(int icdev,unsigned char _Adr,unsigned char *_Data);
int _stdcall lc_read_convenient(int icdev, unsigned char blkAddr, unsigned char keyMode,unsigned char* pKey, unsigned char* pData_out);
int _stdcall lc_write(int icdev,unsigned char _Adr,unsigned char *_Data);
int _stdcall lc_write_convenient(int icdev, unsigned char blkAddr,unsigned char keyMode, unsigned char* pKey, unsigned char* pData_in);
int _stdcall lc_updateKey(int icdev, unsigned char secNr, unsigned char* pNewKeyA, unsigned char* pNewCtrlW, unsigned char* pNewKeyB);
int _stdcall lc_halt(int icdev);
int _stdcall lc_initval(int icdev,unsigned char _Adr,unsigned long _Value);
int _stdcall lc_increment(int icdev,unsigned char _Adr,unsigned long _Value);
int _stdcall lc_readval(int icdev,unsigned char _Adr,unsigned long *_Value);
int _stdcall lc_decrement(int icdev,unsigned char _Adr,unsigned long _Value);
int _stdcall lc_restore(int icdev,unsigned char _fromAdr, unsigned char _toAdr);
int _stdcall lc_readTag(int icdev,unsigned char _Adr,unsigned char *_Data);
int _stdcall lc_writeTag(int icdev,unsigned char _Adr,unsigned char *_Data);
int _stdcall lc_tag_authenPwd(int icdev, unsigned char* pKey_in);
//Para:
//tagType: Tag type, 1-ntag213, 2-ntag215, 3-ntag216
//pPwd: Password, 4 bytes
//protectType: 1-write only, 2-read&write
//protectStartAddr: The address of page start been protect
//maxErrorVerify: The max time verify invalid password continuly,0-Ever(No limit)
//lockConfigAfterSet: Wheather lock configure after setting,TRUE:yes, FALSE:no
int _stdcall lc_tag_setPwd(int icdev, unsigned char tagType,
	unsigned char* pPwd_in,
	unsigned char  protectType,
	unsigned char protectStartAddr,
	unsigned char maxErrorVerify,
	BOOL	lockConfigAfterSet);

/***************
 * Function: Convert card SN to a password
 * Para:
 * pKey: In, the key for cipher, must be 16 bytes
 * cardSN: In,the card number data for cipher
 * snSize: The size of card number data (Bytes)
 * acKeySize: In, the length of pass want return
 * pPass: Out, the returned result
 ***************/
int _stdcall _cardNumberToAccessPass (unsigned char* pKey, unsigned char* pCardSN, int snSize,
	int acKeySize, unsigned char* pPass);

//Utrlight-C
int _stdcall lc_ultralt_C_authen(int icdev, unsigned char* key);
int _stdcall lc_ultralt_C_setSafePage(int icdev, int ipage, BOOL readSec);
int _stdcall lc_ultralt_C_changePwd(int icdev, unsigned char* keyold,
									unsigned char* keynew);
int _stdcall lc_ultralt_C_lockPage(int icdev, int flag);

int __stdcall
lc_pro_reset
(
 int ICDev,//Handle of device
 unsigned char *rlen,//The length of reset information
 unsigned char * rbuff//Reset information
 );

int __stdcall
lc_pro_commandlink
(
 int ICDev,//Handle of device
 unsigned int slen,//The length of data to send
 unsigned char * sbuff,//Data to send
 unsigned int *rlen,//The length of data received
 unsigned char * rbuff,//The data received
 unsigned char tt,//Time for wait when transfering(Unit:10ms)
 unsigned char FG//Section length when transfering(Small than 64)
 );
int _stdcall lc_rawExchange(int icdev,unsigned char slen,unsigned char * sbuff,unsigned char *rrlen,unsigned char * rbuff);
/* getMode: 0-Once every time each card,1-Can read many times one card */
int _stdcall lc_getPBOC_PAN(int icdev, unsigned char slot, unsigned char getMode, char* pPAN);


//--------------------- ISO14443 desfire  card  Functions ------
int __stdcall lc_authen_desfire(int icdev,unsigned char keyNo, char* 
										key,unsigned char* sessionKey);
int __stdcall lc_authen_desfire_aes(int icdev,unsigned char keyNo, char* 
										key,unsigned char* sessionKey);
int __stdcall lc_getver_desfire(int icdev,unsigned char* rlen,unsigned char* version);
int __stdcall lc_getAIDs_desfire(int icdev,unsigned char* rlen,unsigned char* AIDS);
int __stdcall lc_selectApp_desfire(int icdev,unsigned char* AID);
int __stdcall lc_getKeySetting_desfire(int icdev,unsigned char* rlen,unsigned char*setbuf);
int __stdcall lc_getKeyver_desfire(int icdev,unsigned char keyNo,unsigned char* keyVer);
int __stdcall lc_createApp_desfire(int icdev,unsigned char*AID,unsigned char KeySetting,
										   unsigned char NumOfKey);
int __stdcall lc_delAID_desfire(int icdev,unsigned char* AID);
int __stdcall lc_changeKeySetting_desfire(int icdev,unsigned char newSet,char* sessionKey);
int __stdcall lc_changeKey_desfire(int icdev,unsigned char* sessionKey,unsigned char* curKey,
										   unsigned char keyNo,unsigned char* newkey);
int __stdcall lc_changeKey_desfire_aes(int icdev,unsigned char* sessionKey,unsigned char* curKey,
										   unsigned char keyNo,unsigned char* newkey,unsigned char keyVersion);
int __stdcall lc_getFileIDs_desfire(int icdev,unsigned char* rlen,unsigned char* fileIDs);
int __stdcall lc_getFileProper(int icdev,unsigned char fileNo,unsigned char* rlen,
									   unsigned char * fileProper);
int __stdcall lc_changeFileSetting(int icdev,unsigned char fileNo,unsigned char comSet,
										   unsigned char* accessRight,char* sessionKey);
int __stdcall lc_createDataFile_desfire(int icdev,unsigned char fileNo,unsigned char ComSet,
												unsigned char* AccessRight,unsigned char* FileSize);
int __stdcall lc_createBackupDataFile_desfire(int icdev,unsigned char fileNo,unsigned char ComSet,
												unsigned char* AccessRight,unsigned char* FileSize);
int __stdcall lc_createValueFile_desfire(int icdev,unsigned char fileNo,unsigned char ComSet,
												 unsigned char* AccessRight,unsigned char*
												 lowerLimit,unsigned char* upperLimit,unsigned
												 char* value,unsigned char creditEnabled);
int __stdcall lc_createCsyRecord_desfire(int icdev,unsigned char fileNo,unsigned char comSet,
												 unsigned char* AccessRight,unsigned char* RecordSize,
												 unsigned char* MaxNum);
int __stdcall lc_delFile_desfire(int icdev,unsigned char fileNo);
int __stdcall lc_write_desfire(int icdev,unsigned char fileNo,unsigned int offset,unsigned int length,
									   unsigned char* data,char*sessionKey);
int __stdcall lc_read_desfire(int icdev,unsigned char fileNo,unsigned int offset,unsigned int length,
									  unsigned char* revData,char*sessionKey);
int __stdcall lc_getvalue_desfire(int icdev,unsigned char fileNo,
										  unsigned int* value,char* sessionKey);
int __stdcall lc_credit_desfire(int icdev,unsigned char fileNo,
										unsigned int value,char*sessionKey);
int __stdcall lc_debit_desfire(int icdev,unsigned char fileNo,
									   unsigned int value,char*sessionKey);
int __stdcall lc_writeRecord_desfire(int icdev,unsigned char fileNo,
											 unsigned int offset,unsigned int length,
											 unsigned char* data,char*sessionKey);
int __stdcall lc_readRecord_desfire(int icdev,unsigned char fileNo,
											unsigned int offset,unsigned int length,
											unsigned char* revData,unsigned int* SgRecordlen,
											unsigned int*rlen,char*sessionKey);
int __stdcall lc_clearRecord_desfire(int icdev,unsigned char fileNo);
int __stdcall lc_commitTransfer_desfire(int icdev);
int __stdcall lc_abortTransfer_desfire(int icdev);
int __stdcall lc_formatPICC_desfire(int icdev);

//--------------------- Mifare plus  card  Functions ------
int _stdcall lc_MFPlusL0_WritePerso(int icdev, unsigned char* key, unsigned short keyAddr);
int _stdcall lc_MFPlusL0_CommitPerso(int icdev);
int _stdcall lc_MFPlusL1_AuthenKeyL1(int icdev,unsigned char* key);
int _stdcall lc_MFPlusL1_SwitchToL2(int icdev,unsigned char* key);
int _stdcall lc_MFPlusL1_SwitchToL3(int icdev,unsigned char* key);
int _stdcall lc_MFPlusL2_SwitchToL3(int icdev,unsigned char* key);
int _stdcall lc_MFPlusL3_AuthenL3Key(int icdev,unsigned char* key, unsigned short keyAddr);
int _stdcall lc_MFPlusL3_AuthenSectorKey(int icdev,unsigned char keyType,unsigned int sectorNo,unsigned char* key);
int _stdcall lc_MFPlusL3_UpdateKey(int icdev, unsigned int keyAddr,unsigned char* newKey);
int _stdcall lc_MFPlusL3_ReadWithEncrypt(int icdev, unsigned int blkAddr,unsigned char blkNum,
												unsigned char* rdata,unsigned char flag);
int _stdcall lc_MFPlusL3_WriteWithEncrypt(int icdev, unsigned int blkAddr,unsigned char blkNum,
											  unsigned char* wdata,unsigned char flag);
int _stdcall lc_MFPlusL3_ReadWithPlain(int icdev, unsigned int blkAddr,unsigned char blkNum,
											  unsigned char* rdata);
int _stdcall lc_MFPlusL3_WriteWithPlain(int icdev, unsigned int blkAddr,unsigned char blkNum,
											  unsigned char* wdata);
int _stdcall lc_MFPlusL3_InitVal(int icdev, unsigned int blkAddr,unsigned long value);
int _stdcall lc_MFPlusL3_ReadVal(int icdev, unsigned int blkAddr,unsigned long* value);
int _stdcall lc_MFPlusL3_Increment(int icdev, unsigned int blkAddr,unsigned long value);
int _stdcall lc_MFPlusL3_Decrement(int icdev, unsigned int blkAddr,unsigned long value);

//----------------------------- Typeb --------------
int _stdcall lc_findTypeB(int icdev,unsigned char fSelectCard,unsigned char *response_out, unsigned char* resLen_out);
int _stdcall lc_typeB_command
(
 int ICDev,//Handle of device
 unsigned int slen,//The length of data to send
 unsigned char * sbuff,//Data to send
 unsigned int *rlen,//The length of data received
 unsigned char * rbuff//The data received
 );
//----------------------------- ISO15693 --------------
/* reqMode: The mode when finding card, 0x36-Single card mode, 0x16-Multiple card mode*/
int _stdcall lc_find15693(
	int icdev,
	unsigned char reqMode, 
	unsigned char *response_out, 
	unsigned char* resLen_out);
int _stdcall lc_15693_command
(
 int ICDev,//Handle of device
 unsigned char cmd, //The command to send
 unsigned char* pUID, //The id of card (8 bytes)
 unsigned int sParaLen,//The length of paramter 
 unsigned char * psPara,//Paramter 
 unsigned int *rParaLen,//The length of paramter received
 unsigned char * rPara//The parater received
 );
int _stdcall lc_15693_command_custom
(
 int ICDev,//Handle of device
 unsigned char cmd, //The command to send
 unsigned char MfgCode, //IC Mfg code
 unsigned char* pUID, //The id of card (8 bytes)
 unsigned int sParaLen,//The length of paramter 
 unsigned char * psPara,//Paramter 
 unsigned int *rParaLen,//The length of paramter received
 unsigned char * rPara//The parater received
 );
int _stdcall lc_15693_stay_quiet(
	int icdev,
	unsigned char *pUID);
int _stdcall lc_15693_select_uid(
	int icdev,
	unsigned char *pUID);
int _stdcall lc_15693_reset_to_ready(
	int icdev,
	unsigned char *pUID);
int _stdcall lc_15693_readBlock(
	int icdev,
	unsigned char *pUID,
	unsigned char startBlock,
	unsigned char blockNum,
	unsigned char *rlen,
	unsigned char *rbuffer);
int _stdcall lc_15693_writeBlock(
	int icdev,
	unsigned char *pUID,
	unsigned char startBlock,
	unsigned char blockNum, 
	unsigned char wlen,
	unsigned char *wbuffer);
int _stdcall lc_15693_lock_block(
	int icdev,
	unsigned char *pUID,
	unsigned char block);
int _stdcall lc_15693_write_afi(
	int icdev,
	unsigned char *pUID,
	unsigned char AFI);
int _stdcall lc_15693_lock_afi(
	int icdev,
	unsigned char *pUID);
int _stdcall lc_15693_write_dsfid(
	int icdev,
	unsigned char *pUID,
	unsigned char DSFID);
int _stdcall lc_15693_lock_dsfid(
	int icdev,
	unsigned char *pUID);
int _stdcall lc_15693_get_systemInfo(
	int icdev,
	unsigned char *pUID,
	unsigned char *rlen,
	unsigned char *rbuffer);
int _stdcall lc_15693_get_securityInfo(
	int icdev,
	unsigned char *pUID,
	unsigned char startBlock,
	unsigned char blockNum,
	unsigned char *rlen,
	unsigned char *rbuffer);
/* pwdType:01h-Read, 02h-Write, 04h-Privacy,08h-Destroy SLI-L, 10h-EAS */
int _stdcall lc_15693set_password(
	int icdev,
	unsigned char *pUID, 
	unsigned char pwdType, 
	unsigned char* pPwd);
/* pwdType:01h-Read, 02h-Write,04h-Privacy,08h-Destroy SLI-L, 10h-EAS , and privacy is default used*/
int _stdcall lc_15693_write_password(
	int icdev,
	unsigned char *pUID, 
	unsigned char pwdType, 
	unsigned char* pPwd);
int _stdcall lc_15693_icode_64bitProtect(int icdev,unsigned char *pUID);
/*protectStatus:00h-Public,01h-Read and write protect by read-pass, 10h-Write protect by wirte pass. 
	11h-Read protect by the read pass, and Write protect by write pass*/
int _stdcall lc_15693_protect_page(
	int icdev,
	unsigned char *pUID, 
	unsigned char iPage, 
	unsigned char protectStatus);

//----------------------------- TypeF --------------
int _stdcall lc_findTypeF(int icdev,unsigned short sysCode,unsigned char *pIDm_out, unsigned char* pPMm_out);
int _stdcall lc_typeF_command
(
 int icdev,//Handle of device
 unsigned int slen,//The length of data to send
 unsigned char * sbuff,//Data to send
 unsigned int *rlen,//The length of data received
 unsigned char * rbuff//The data received
 );

//----------------------------- ICC ------------------------------------------------------------

//########### CARD TYPES ##############
#define SLOT_ICC_MSR			0x00
#define SLOT_ICC_SAM1			0x01
#define SLOT_ICC_SAM2			0x02
#define SLOT_ICC_SAM3			0x03
#define SLOT_ICC_SAM4			0x04
#define SLOT_ICC_SAM5			0x05
#define SLOT_ICC_SAM6			0x06
#define SLOT_ICC_SAM7			0x07
#define SLOT_ICC_SAM8			0x08


//########### CARD TYPES ##############
#define CARD_AT24XX	 			0x01
#define	CARD_AT24C64 			0x02
#define	CARD_4442	 			0x03
#define	CARD_4428	 			0x04
#define	CARD_CPU	 			0x0C

int _stdcall lc_iccGetCardState(int icdev,unsigned char slot, unsigned char *pSt);
int _stdcall lc_iccSelCardType
(
 int ICDev,//Handle of device
 unsigned char slot,
 unsigned int cardType
 );
int _stdcall lc_iccSetBaud(int icdev, unsigned char slot, unsigned int baud);
int _stdcall lc_iccGetATR(int icdev,unsigned char slot, unsigned char *response_out, unsigned char* resLen_out);
int _stdcall lc_iccPPS(int icdev, unsigned char slot, unsigned char* pPara);
int _stdcall lc_icc_APDU
(
 int ICDev,//Handle of device
 unsigned char slot,
 unsigned int slen,//The length of data to send
 unsigned char * sbuff,//Data to send
 unsigned int *rlen,//The length of data received
 unsigned char * rbuff//The data received
 );
int _stdcall lc_icc_ReadMem
(
 int ICDev,//Handle of device
 unsigned char slot,
 unsigned int  address,
 unsigned int  rLen,
 unsigned char * rbuff//The data received
 );
int _stdcall lc_icc_WriteMem
(
 int ICDev,//Handle of device
 unsigned char slot,
 unsigned int  address,
 unsigned int  wLen,
 unsigned char * wbuff
 );
int _stdcall lc_icc_VerifyUserPass
(
 int ICDev,//Handle of device
 unsigned char slot,
 unsigned int  passLen,
 unsigned char * pPassIn
 );
int _stdcall lc_icc_ReadErrorCounter(
	int ICDev, 
	unsigned char slot,
	unsigned char* pCnt);

int _stdcall lc_icc_UpdateUserPass
(
 int ICDev,//Handle of device
 unsigned char slot,
 unsigned int  passLen,
 unsigned char * pPassIn
 );
#ifdef __cplusplus
}
#endif

#endif
