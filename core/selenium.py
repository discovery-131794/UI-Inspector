from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import time

TIMEOUT = 60

class RpaElement(WebElement):

    def find_element(self, by, locator, timeout=TIMEOUT, before_delay=0):
        """
        通过不同定位器查找子元素，定位器类型可以为'id', 'class_name', 'tag_name', 'name', 'css', 'xpath'

        :Args:
         - by - 定位器类型
         - locator - 定位器值
         - timeout - 查找元素超时时间，默认为60s
         - before_delay - 查找元素前的延时，默认为0 

         return：RpaElement
        """
        time.sleep(before_delay)
        try:
            if by=='id':
                return WebDriverWait(self, timeout).until(lambda d : WebElement.find_element(d, By.ID, locator))
            elif by=='class_name':
                return WebDriverWait(self, timeout).until(lambda d : WebElement.find_element(d, By.CLASS_NAME, locator))
            elif by=='tag_name':
                return WebDriverWait(self, timeout).until(lambda d : WebElement.find_element(d, By.TAG_NAME, locator))
            elif by=='name':
                return WebDriverWait(self, timeout).until(lambda d : WebElement.find_element(d, By.NAME, locator))
            elif by=='css':
                return WebDriverWait(self, timeout).until(lambda d : WebElement.find_element(d, By.CSS_SELECTOR, locator))
            else:
                return WebDriverWait(self, timeout).until(lambda d : WebElement.find_element(d, By.XPATH, locator))
        except TimeoutException:
            raise

    def find_elements(self, by, locator, timeout=1, retry=10, before_delay=0):
        """
        通过不同定位器查找子元素集合, 定位器类型可以为'class_name', 'tag_name', 'name', 'css', 'xpath'

        :Args:
         - by - 定位器类型
         - locator - 定位器值
         - timeout - 每次重试时的延迟时间，默认为1s
         - retry - 重试次数
         - before_delay - 查找元素前的延时时间，默认为0

         return: RpaElement列表
        """
        time.sleep(before_delay)
        ele_list = []
        while retry > 0:
            if by=='id':
                ele_list = super().find_elements(By.ID, locator)
            elif by=='class_name':
                ele_list = super().find_elements(By.CLASS_NAME, locator)
            elif by=='tag_name':
                ele_list = super().find_elements(By.TAG_NAME, locator)
            elif by=='name':
                ele_list = super().find_elements(By.NAME, locator)
            elif by=='css':
                ele_list = super().find_element(By.CSS_SELECTOR, locator)
            else:
                ele_list = super().find_elements(By.XPATH, locator)
            if not ele_list:
                time.sleep(timeout)
            else:
                break
            retry -= 1
        
        return ele_list

    


class RpaDriver(WebDriver):
    
    _web_element_cls = RpaElement
    
    def find_element(self, by, locator, timeout=TIMEOUT, before_delay=0) -> RpaElement:
        """
        通过不同定位器查找元素, 定位器类型可以为'id', 'class_name', 'tag_name', 'name', 'css', 'xpath'

        :Args:
         - by - 定位器类型
         - locator - 定位器值
         - timeout - 查找元素超时时间，默认为60s
         - before_delay - 查找元素前的延时，默认为0 

         return: RpaElement
        """
        time.sleep(before_delay)
        try:
            if by=='id':
                return WebDriverWait(self, timeout).until(lambda d : WebDriver.find_element(d, By.ID, locator))
            elif by=='class_name':
                return WebDriverWait(self, timeout).until(lambda d : WebDriver.find_element(d, By.CLASS_NAME, locator))
            elif by=='tag_name':
                return WebDriverWait(self, timeout).until(lambda d : WebDriver.find_element(d, By.TAG_NAME, locator))
            elif by=='name':
                return WebDriverWait(self, timeout).until(lambda d : WebDriver.find_element(d, By.NAME, locator))
            elif by=='css':
                return WebDriverWait(self, timeout).until(lambda d : WebDriver.find_element(d, By.CSS_SELECTOR, locator))
            else:
                return WebDriverWait(self, timeout).until(lambda d : WebDriver.find_element(d, By.XPATH, locator))
        except TimeoutException:
            raise

    def find_elements(self, by, locator, timeout=1, retry=10, before_delay=0):
        """
        通过不同定位器查找元素集合, 定位器类型可以为'class_name', 'tag_name', 'name', 'css', 'xpath'

        :Args:
         - by - 定位器类型
         - locator - 定位器值
         - timeout - 每次重试时的延迟时间，默认为1s
         - retry - 重试次数
         - before_delay - 查找元素前的延时时间，默认为0

         return: RpaElement列表
        """
        time.sleep(before_delay)
        ele_list = []
        while retry > 0:
            if by=='id':
                ele_list = super().find_elements(By.ID, locator)
            elif by=='class_name':
                ele_list = super().find_elements(By.CLASS_NAME, locator)
            elif by=='tag_name':
                ele_list = super().find_elements(By.TAG_NAME, locator)
            elif by=='name':
                ele_list = super().find_elements(By.NAME, locator)
            elif by=='css':
                ele_list = super().find_elements(By.CSS_SELECTOR, locator)
            else:
                ele_list = super().find_elements(By.XPATH, locator)
            if not ele_list:
                time.sleep(timeout)
            else:
                break
            retry -= 1
        
        return ele_list

    def execute_script(self, script, *args, before_delay=0.5):
        """
        延迟执行js脚本

        :Args:
         - script - 脚本字符串
         - *args - 脚本参数
         - before_delay - 执行脚本前的延时时间，默认为0
        """
        time.sleep(before_delay)
        return super().execute_script(script, *args)
    
