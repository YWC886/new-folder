/**
  ***********************************************************************************************************
 
  ***********************************************************************************************************
  * @attention
  *
  *
  ***********************************************************************************************************
  */
 
/**
  ***********************************************************************************************************
  * ͷ�ļ�
  * ********************************************************************************************************* 
  */ 
#include "can.h"

 /**
  ***********************************************************************************************************
  * 
  * ********************************************************************************************************* 
  */ 
	
extern uint8_t timer_1ms_Flag;
extern ANALOG_UDT analog;
extern HALL_TO_ANGLE_UDT    hall2angle;

S_CAN_MSG_ESC_STAT1  CanData_Stat_1  = DEF_CAN_DATA_STAT1;
S_CAN_MSG_ESC_STAT2  CanData_Stat_2  = DEF_CAN_DATA_STAT2;
S_CAN_MSG_ESC_STAT3  CanData_Stat_3  = DEF_CAN_DATA_STAT3;
S_CAN_MSG_ESC_STAT4  CanData_Stat_4  = DEF_CAN_DATA_STAT4;
S_CAN_MSG_ESC_STAT5  CanData_Stat_5  = DEF_CAN_DATA_STAT5; 
S_CAN_ESC_CMD CanEscCmd = {0};
uint16_t Thread_CMD = 0;

uint8_t My_node_id = NOTE_ID;
uint8_t CanDataUpEnble = 1;
uint8_t CanSendBuf[8] = {0};
uint8_t CanTransferIDBuf[5] = {0};  //������ͬDataTypeID �����ݣ�ÿ����һ�����ݣ�TransferID��1��0~31 ѭ���ۼӡ�
  
 

uint8_t CanDataUpTime = 0, CanDataUpTimes = 2, CanDataUpIndex = 0;


uint16_t MessageTypeIDBuf[6] = {1150, 1151, 1152, 1153, 1154, 999}; 


/****************************************************************/ 
void CanDataUpFerSet(pamr)
{
  switch (pamr)
  {
    case 0:
      CanDataUpTimes = 20;
      break;
    case 1:
      CanDataUpTimes = 40;
      break;
    case 2:
      CanDataUpTimes = 200;
      break;  
    default:
      break;
  }
}
/*****************************************************************
  *  @brief  can1 interrupt function tx1
  *  @param  none
  *  @retval none
  */
 void USBFS_H_CAN1_TX_IRQnHandler (void)
 {
    if(can_interrupt_flag_get(CAN1,CAN_TMEF_FLAG) != RESET)
    {
      can_flag_clear(CAN1, CAN_TMEF_FLAG); 
    }
 }
 
uint16_t GetEscCmd(void)
{
  uint8_t id = My_node_id & 0x07;
  uint16_t cmd;

  switch (id) //ֻȡ��3λ
  {
    case 0x01:
      if ((CanEscCmd.chan1_enable == 1) && (CanEscCmd.chan1_node_id == id)) cmd = CanEscCmd.chan1_thr_cmd;  
      break;
    case 0x02:
      if ((CanEscCmd.chan2_enable == 1) && (CanEscCmd.chan2_node_id == id)) cmd = CanEscCmd.chan2_thr_cmd;  
      break;
    case 0x03:
      if ((CanEscCmd.chan3_enable == 1) && (CanEscCmd.chan3_node_id == id)) cmd = CanEscCmd.chan3_thr_cmd;  
      break;
    case 0x04:
      if ((CanEscCmd.chan4_enable == 1) && (CanEscCmd.chan4_node_id == id)) cmd = CanEscCmd.chan4_thr_cmd;  
      break;    
    default:
      break;
  }
  return cmd;
}
/*****************************************************************
  *  @brief  can1 interrupt function rx1
  *  @param  none
  *  @retval none
  * 
  * �ݶ������·���ʽ AA 55 CMD Pram 00 00 00 TailByte�� 
  *                       01 ���� ID          Pram��ID
  *                       02 �����������ȼ�    Pram��0 PWM����  1������������  
  *                       03 ����CAN���߲����� Pram��0-1MBPS 1-500KBPS 2-250KBPS 3-125KBPS 4-100KBPS5-50KBPS 
  *                       04 �����ϱ�����      Pram��0-10Hz  1-5Hz  2-1Hz
  *                       05 �Լ��ѯ          Pram����  
  */
void CAN1_RX1_IRQHandler (void)
{
  can_rx_message_type rx_message_struct;
  if(can_interrupt_flag_get(CAN1,CAN_RF1MN_FLAG) != RESET)
  {
    can_message_receive(CAN1, CAN_RX_FIFO1, &rx_message_struct);
    if (rx_message_struct.extended_id == 1160) //�������� Messags-type-ID = 1160
    {
      if (CanData_Stat_1.esc_mode.bit.thr_pri == 1)
      {   
        memcpy(&CanEscCmd, rx_message_struct.data, 8);   // 8 �ֽڣ���λ��ṹ��Ҳ ���� 64 bit��8 byte��
        Thread_CMD = GetEscCmd();
      }
    }

    if(rx_message_struct.extended_id == 1000)  //Messags-type-ID = 1000
    {
      if ((rx_message_struct.data[0] == 0xAA) && (rx_message_struct.data[1] == 0x55))
      {
        uint8_t cmd = rx_message_struct.data[2];
        uint8_t pamr = rx_message_struct.data[3];
        switch (cmd)
        {
          case 0x01:
            My_node_id = pamr;
            break;
          case 0x02:
            CanData_Stat_1.esc_mode.bit.thr_pri = pamr;
            break;
          case 0x03:
            CanBaudRateSet(pamr);
            break;
          case 0x04:
            CanDataUpFerSet(pamr);
            break;  
          case 0x05:              
            break;            
          default:
            break;
        } 
      } 
    }
	}    
}



/********************************************************************
  *  @brief  can1 interrupt function se
  *  @param  none
  *  @retval none
  */
void CAN1_SE_IRQHandler(void)  /* CAN1 ״̬�����ж� */
{
  __IO uint32_t err_index = 0;
  if(can_interrupt_flag_get(CAN1,CAN_ETR_FLAG) != RESET)
  {
    err_index = CAN1->ests & 0x70;
    can_flag_clear(CAN1, CAN_ETR_FLAG);
    /* error type is stuff error */
    if(err_index == 0x00000010)
    {
      /* when stuff error occur: in order to ensure communication normally,
      user must restart can or send a frame of highest priority message here */
    }
  }
}
/**
  *  @brief  can transmit data
  *  @param  none
  *  @retval none
  */
void can_transmit_data(uint32_t id, uint8_t len)
{
  uint8_t transmit_mailbox;
  can_tx_message_type tx_message_struct;
  tx_message_struct.standard_id = id;
  tx_message_struct.extended_id = 0;
  tx_message_struct.id_type = CAN_ID_STANDARD;
  tx_message_struct.frame_type = CAN_TFT_DATA;
  tx_message_struct.dlc = len;
  uint8_t i;
  for(i = 0; i < len; i++) tx_message_struct.data[i] = CanSendBuf[i];
	
  transmit_mailbox = can_message_transmit(CAN1, &tx_message_struct);
  while(can_transmit_status_get(CAN1, (can_tx_mailbox_num_type)transmit_mailbox) != CAN_TX_STATUS_SUCCESSFUL);
}
 

 
/*******************************************************/
void can_transmit_CanDataStat(uint8_t stat)
{
  CAN_MSG_ID  Can_Msg_ID;
  uint8_t index;
  index = CanDataUpIndex;

  if (++CanTransferIDBuf[index] >= 32) CanTransferIDBuf[index] = 0;

  Can_Msg_ID.ID = 0;
  Can_Msg_ID.ID_Bit.Message_type_id = MessageTypeIDBuf[index];
  Can_Msg_ID.ID_Bit.Source_node_id = My_node_id;

  switch (index)
  {
    case 0x00:  //״̬1
      CanData_Stat_1.esc_mode.bit.can_thr_online = 1;
			CanData_Stat_1.esc_mode.bit.pwm_thr_online = 1;
      CanData_Stat_1.esc_mode.bit.thr_pri = 0; 
      CanData_Stat_1.spd_rpm = hall2angle.pll_speed_rpm_filter; 
      memcpy(CanSendBuf, &CanData_Stat_1, sizeof(CanData_Stat_1) -1);
      break;
    case 0x01:  //״̬2
      CanData_Stat_2.vdc_100mv = (int16_t)(analog.volt_filter * 10);
      CanData_Stat_2.irms_100ma = 0;
      CanData_Stat_2.idq0_100ma = 0;
      memcpy(CanSendBuf, &CanData_Stat_2, sizeof(CanData_Stat_2) -1);       
      break;    
    case 0x02:  //״̬3
      CanData_Stat_3.alg_err = 0;
      CanData_Stat_3.alg_warn = 0;
      CanData_Stat_3.vdq0_duty = 0;
      memcpy(CanSendBuf, &CanData_Stat_3, sizeof(CanData_Stat_3) -1);
      break;    
    case 0x03:  //״̬4 
      CanData_Stat_4.mos_temp = 250;
      CanData_Stat_4.idq1_100ma = 0; //��2·�������Ϊ��
      CanData_Stat_4.vdq1_duty  = 0; //��2·�������Ϊ��
      memcpy(CanSendBuf, &CanData_Stat_4, sizeof(CanData_Stat_4) -1);
      break;    
    case 0x04:  //״̬5
      CanData_Stat_5.idc = 0;
      CanData_Stat_5.cap_temp = 0; //��ʵ���Ϊ��
      CanData_Stat_5.motor_temp = 0; 
      memcpy(CanSendBuf, &CanData_Stat_5, sizeof(CanData_Stat_5) -1);
      break;
    default:
        break;            
  }

  CanSendBuf[7] = 0xC0 | CanTransferIDBuf[index];  //Start of transfer,End of transfer��Toggle bit ��֡����ʱ�̶�Ϊ 110.
    
  can_tx_message_type tx_message_struct;
  tx_message_struct.standard_id = 0;
  tx_message_struct.extended_id = Can_Msg_ID.ID;
  tx_message_struct.id_type = CAN_ID_EXTENDED;
  tx_message_struct.frame_type = CAN_TFT_DATA;
  tx_message_struct.dlc = 8; 
  memcpy(tx_message_struct.data, CanSendBuf, 8);
	
  uint8_t transmit_mailbox = can_message_transmit(CAN1, &tx_message_struct);
  while(can_transmit_status_get(CAN1, (can_tx_mailbox_num_type)transmit_mailbox) != CAN_TX_STATUS_SUCCESSFUL);
}
/*******************************************************/
void can_updata(void)
{
	if (CanDataUpEnble == 1)
	{		
		if (timer_1ms_Flag == 1)
		{			
			timer_1ms_Flag = 0;
			if (++CanDataUpTime >= CanDataUpTimes) //2ms ����һ֡����5֡
			{
				CanDataUpTime = 0;

				if (++CanDataUpIndex >= 5) CanDataUpIndex = 0;
				can_transmit_CanDataStat(CanDataUpIndex);
			}    
		}
	}
}


































/************************************* (C) COPYRIGHT mandzy *******END OF FILE******************************/

