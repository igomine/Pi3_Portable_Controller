/**
******************************************************************************
* @file    USART/USART_Printf/main.c 
* @author  MCD Application Team
* @version V1.4.0
* @date    24-July-2014
* @brief   Main program body
******************************************************************************
* @attention
*
* <h2><center>&copy; COPYRIGHT 2014 STMicroelectronics</center></h2>
*
* Licensed under MCD-ST Liberty SW License Agreement V2, (the "License");
* You may not use this file except in compliance with the License.
* You may obtain a copy of the License at:
*
*        http://www.st.com/software_license_agreement_liberty_v2
*
* Unless required by applicable law or agreed to in writing, software 
* distributed under the License is distributed on an "AS IS" BASIS, 
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
*
******************************************************************************
*/

/* Includes ------------------------------------------------------------------*/
#include "stm32f0xx.h"
#include <stdio.h>

/* Private define ------------------------------------------------------------*/
//角位移传感器端口定义
#define PORT_DS	(GPIOF)
#define _DATA	(GPIO_Pin_0)
#define _SCLK	(GPIO_Pin_1)
#define PORT_CS	(GPIOA)
#define _CS		(GPIO_Pin_0)
//限位状态指示灯端口定义
#define PORT_Limit_L	(GPIOB)
#define PORT_Q0		(GPIO_Pin_1)
#define PORT_Limit_R	(GPIOA)
#define PORT_Q2		(GPIO_Pin_4)
#define PORT_Limit_M	(GPIOA)
#define PORT_Q1		(GPIO_Pin_9)

//限位状态输出端口定义
#define PORT_QOUT	(GPIOA)
#define PORT_Q00	(GPIO_Pin_7)
#define PORT_Q01	(GPIO_Pin_6)
#define PORT_Q02	(GPIO_Pin_5)

//复位按钮开关状态端口定义
#define PORT_RSW	(GPIOA)
#define PORT_SW0	(GPIO_Pin_1)
#define PORT_SW1	(GPIO_Pin_2)
#define PORT_SW2	(GPIO_Pin_3)

/* Private macro -------------------------------------------------------------*/
/* Private variables ---------------------------------------------------------*/
/* Private function prototypes -----------------------------------------------*/
static void GPIO_Config(void);

/* Private functions ---------------------------------------------------------*/
void Delay(uint32_t time);

void Write5012(uint16_t cmd);
void Read_AngValue(void);
void WriteFlash(void);
uint32_t ReadFlash(uint16_t addr);
void BSP_Init(void);              //板级支持包初始化
uint16_t KEY=0;
_Bool DIR = 0;
_Bool WORK = 0;
uint32_t ang_val=0;
uint32_t ang_val0;
uint32_t ang_val1;
uint32_t ang_val2;

uint32_t tmp=0;
uint32_t tmp_crc=0;
uint32_t FLASH_START_ADDR = 0x08000000+1024*8;
/**
* @brief  Main program
* @param  None
* @retval None
*/
int main(void)
{    
	BSP_Init();
	while(1)
	{
		Write5012(0x8021);
		Read_AngValue();
		Delay(10000);
	}
}

/**
* @brief Configure the USART Device
* @param  None
* @retval None
*/
static void GPIO_Config(void)
{
	GPIO_InitTypeDef GPIO_InitStructure;
	/* Enable GPIO clock */
	RCC_AHBPeriphClockCmd(RCC_AHBPeriph_GPIOA, ENABLE);
	RCC_AHBPeriphClockCmd(RCC_AHBPeriph_GPIOB, ENABLE);
	RCC_AHBPeriphClockCmd(RCC_AHBPeriph_GPIOF, ENABLE);
    //初始化角位移传感器端口
	GPIO_InitStructure.GPIO_Pin = _DATA|_SCLK;
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_OUT;
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
	GPIO_InitStructure.GPIO_OType = GPIO_OType_PP;
	GPIO_InitStructure.GPIO_PuPd = GPIO_PuPd_UP;
	GPIO_Init(PORT_DS, &GPIO_InitStructure);
	
	GPIO_InitStructure.GPIO_Pin = _CS;
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_OUT;
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
	GPIO_InitStructure.GPIO_OType = GPIO_OType_PP;
	GPIO_InitStructure.GPIO_PuPd = GPIO_PuPd_UP;
	GPIO_Init(PORT_CS, &GPIO_InitStructure);
	
	
	//初始化限位状态指示灯端口
	GPIO_InitStructure.GPIO_Pin = PORT_Q0;
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_OUT;
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
	GPIO_InitStructure.GPIO_OType = GPIO_OType_PP;
	GPIO_InitStructure.GPIO_PuPd = GPIO_PuPd_UP;
	GPIO_Init(PORT_Limit_L, &GPIO_InitStructure);
	GPIO_SetBits(PORT_Limit_L,PORT_Q0);
	
	GPIO_InitStructure.GPIO_Pin = PORT_Q1;
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_OUT;
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
	GPIO_InitStructure.GPIO_OType = GPIO_OType_PP;
	GPIO_InitStructure.GPIO_PuPd = GPIO_PuPd_UP;
	GPIO_Init(PORT_Limit_M, &GPIO_InitStructure);
	GPIO_SetBits(PORT_Limit_M,PORT_Q1);
	
	GPIO_InitStructure.GPIO_Pin = PORT_Q2;
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_OUT;
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
	GPIO_InitStructure.GPIO_OType = GPIO_OType_PP;
	GPIO_InitStructure.GPIO_PuPd = GPIO_PuPd_UP;
	GPIO_Init(PORT_Limit_R, &GPIO_InitStructure);
	GPIO_SetBits(PORT_Limit_R,PORT_Q2);
	//初始化输出开关状态端口
	GPIO_InitStructure.GPIO_Pin = PORT_Q00|PORT_Q01|PORT_Q02;
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_OUT;
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
	GPIO_InitStructure.GPIO_OType = GPIO_OType_PP;
	GPIO_InitStructure.GPIO_PuPd = GPIO_PuPd_UP;
	GPIO_Init(PORT_QOUT, &GPIO_InitStructure);
	
	
	//初始化复位按钮开关状态端口
	GPIO_InitStructure.GPIO_Pin = PORT_SW0|PORT_SW1|PORT_SW2;
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IN;
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
	GPIO_InitStructure.GPIO_OType = GPIO_OType_OD;
	GPIO_InitStructure.GPIO_PuPd = GPIO_PuPd_NOPULL;
	GPIO_Init(PORT_RSW, &GPIO_InitStructure);
}


void Delay(uint32_t time)
{
	while(time--)
	{
		KEY = GPIO_ReadInputData(GPIOA)&0x000E;
		if((KEY&0x0002)==0x0002)
		{
			GPIO_SetBits(PORT_Limit_R,PORT_Q2);
			ang_val0=ReadFlash(0);
			if(ang_val>=(ang_val0-300)&&ang_val<=(ang_val0+300))
			{
				GPIO_SetBits(PORT_QOUT,PORT_Q02);
				GPIO_ResetBits(PORT_Limit_R,PORT_Q2);
			}
			else
			{
				GPIO_ResetBits(PORT_QOUT,PORT_Q02);
			}
		}
		else
		{
			GPIO_ResetBits(PORT_Limit_R,PORT_Q2);
			GPIO_SetBits(PORT_QOUT,PORT_Q02);
			ang_val0=ang_val;
			WriteFlash();
		}
		if((KEY&0x0004)==0x0004)
		{
			GPIO_SetBits(PORT_Limit_M,PORT_Q1);
			ang_val1=ReadFlash(1);
			if(ang_val>=(ang_val1-300)&&ang_val<=(ang_val1+300))
			{
				GPIO_SetBits(PORT_QOUT,PORT_Q01);
				GPIO_ResetBits(PORT_Limit_M,PORT_Q1);
			}
			else
			{
				GPIO_ResetBits(PORT_QOUT,PORT_Q01);
			}
		}
		else
		{
			GPIO_ResetBits(PORT_Limit_M,PORT_Q1);
			GPIO_SetBits(PORT_QOUT,PORT_Q01);
			ang_val1=ang_val;
			WriteFlash();
		}
		if((KEY&0x0008)==0x0008)
		{
			GPIO_SetBits(PORT_Limit_L,PORT_Q0);
			ang_val2=ReadFlash(2);
			if(ang_val>=(ang_val2-300)&&ang_val<=(ang_val2+300))
			{
				GPIO_SetBits(PORT_QOUT,PORT_Q00);
				GPIO_ResetBits(PORT_Limit_L,PORT_Q0);
			}
			else
			{
				GPIO_ResetBits(PORT_QOUT,PORT_Q00);
			}
		}
		else
		{
			GPIO_ResetBits(PORT_Limit_L,PORT_Q0);
			GPIO_SetBits(PORT_QOUT,PORT_Q00);
			ang_val2=ang_val;
			WriteFlash();
		}
	}
}

void BSP_Init(void)              //板级支持包初始化
{
	/* GPIO configuration */
	GPIO_Config();
}
void Write5012(uint16_t cmd)
{
	char i;
	GPIO_ResetBits(PORT_CS,_CS);
	//Delay(1);
	for(i=0;i<16;i++)
	{
		GPIO_ResetBits(PORT_DS,_SCLK);
		if(cmd&0x8000)
		{
			GPIO_SetBits(PORT_DS,_DATA);
		}
		else
		{
			GPIO_ResetBits(PORT_DS,_DATA);
		}
		GPIO_SetBits(PORT_DS,_SCLK);
		cmd<<=1;
	}
}

void Read_AngValue(void)
{
	char i;
	GPIO_InitTypeDef  GPIO_InitStructure;
	GPIO_InitStructure.GPIO_Pin = _DATA;
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IN;
	GPIO_InitStructure.GPIO_OType = GPIO_OType_OD;
	GPIO_InitStructure.GPIO_PuPd  = GPIO_PuPd_NOPULL;
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
	GPIO_Init(PORT_DS, &GPIO_InitStructure);
 	//GPIO_SetBits(GPIOA,GPIO_Pin_2);
	
	//GPIO_ResetBits(GPIOA,GPIO_Pin_0);
	Delay(1);
	for(i=0;i<16;i++)
	{
		GPIO_SetBits(PORT_DS,_SCLK);
		Delay(1);
		if(GPIO_ReadInputDataBit(PORT_DS,_DATA))
		{
			tmp=tmp|0x0001;
		}
		else
		{
			tmp=tmp&0xfffe;
		}
		//Delay(1);
		GPIO_ResetBits(PORT_DS,_SCLK);
		tmp<<=1;
	} 
	for(i=0;i<16;i++)
	{
		GPIO_ResetBits(PORT_DS,_SCLK);
		Delay(1);
		if(GPIO_ReadInputDataBit(PORT_DS,_DATA))
		{
			tmp_crc=tmp_crc|0x0001;
		}
		else
		{
			tmp_crc=tmp_crc&0xfffe;
		}
		//Delay(1);
		GPIO_SetBits(PORT_DS,_SCLK);
		tmp_crc<<=1;
	}
	GPIO_SetBits(PORT_CS,_CS);
	//Delay(1);
	//if(tmp_crc==cheack_CRC(tmp))
	ang_val = (uint32_t)(tmp&0x7fff);

	GPIO_InitStructure.GPIO_Pin = _DATA;
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_OUT;
	GPIO_InitStructure.GPIO_OType = GPIO_OType_PP;
	GPIO_InitStructure.GPIO_PuPd  = GPIO_PuPd_UP;
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
	GPIO_Init(PORT_DS, &GPIO_InitStructure);
	GPIO_SetBits(PORT_DS,_DATA);
}


void WriteFlash()
{

	FLASH_Unlock(); //解锁FLASH编程擦除控制器
	FLASH_ClearFlag(FLASH_FLAG_BSY|FLASH_FLAG_EOP|FLASH_FLAG_PGERR|FLASH_FLAG_WRPERR);//清除标志位
	FLASH_ErasePage(FLASH_START_ADDR); //擦除指定地址页
	FLASH_ProgramWord(FLASH_START_ADDR+0,ang_val0); //从指定页的0地址开始写	
	FLASH_ClearFlag(FLASH_FLAG_BSY|FLASH_FLAG_EOP|FLASH_FLAG_PGERR|FLASH_FLAG_WRPERR);//清除标志位
	FLASH_ProgramWord(FLASH_START_ADDR+4,ang_val1); //从指定页的0地址开始写
	FLASH_ClearFlag(FLASH_FLAG_BSY|FLASH_FLAG_EOP|FLASH_FLAG_PGERR|FLASH_FLAG_WRPERR);//清除标志位
	FLASH_ProgramWord(FLASH_START_ADDR+8,ang_val2); //从指定页的0地址开始写
	FLASH_ClearFlag(FLASH_FLAG_BSY|FLASH_FLAG_EOP|FLASH_FLAG_PGERR|FLASH_FLAG_WRPERR);//清除标志位
	FLASH_Lock(); //锁定FLASH编程擦除控制器
}
uint32_t ReadFlash(uint16_t addr)
{
uint32_t value;
value = *(uint32_t*)(FLASH_START_ADDR+(addr*4));
return value;
}
#ifdef  USE_FULL_ASSERT

/**
* @brief  Reports the name of the source file and the source line number
*         where the assert_param error has occurred.
* @param  file: pointer to the source file name
* @param  line: assert_param error line source number
* @retval None
*/
void assert_failed(uint8_t* file, uint32_t line)
{ 
  /* User can add his own implementation to report the file name and line number,
  ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  
  /* Infinite loop */
  while (1)
  {
  }
}
#endif

/**
* @}
*/ 

/**
* @}
*/ 

/************************ (C) COPYRIGHT STMicroelectronics *****END OF FILE****/
