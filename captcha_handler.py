import logging
import os
import time
import random
import json
import re
from typing import Optional, Dict

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from openai import OpenAI
from config import Config

logger = logging.getLogger(__name__)


class CaptchaHandler:
    """验证码处理器"""
    
    def __init__(self, config: Config):
        self.config = config
        self.client = OpenAI(
            base_url=config.base_url,
            api_key=config.api_key
        )

    def get_img(self, wait: WebDriverWait):
        try:
            # 获取验证码图片
            captcha_img_element = wait.until(
                EC.visibility_of_element_located((By.CLASS_NAME, "geetest_tip_img"))
            )

            # 获取 CSS 属性
            bg_style = captcha_img_element.value_of_css_property("background-image")
            
            # 正则匹配
            match = re.search(r'url\(["\']?(.*?)["\']?\)', bg_style)
            if match:
                img_url = match.group(1)
                logger.info(f"成功获取验证码图片 URL: {img_url}")
                return img_url
            else:
                logger.error("无法提取验证码图片 URL")
                return ""
        except TimeoutException:
                logger.info("未检测到 GeeTest 验证码窗口")
                return False
    
    def handle_geetest_captcha(self, driver, wait: WebDriverWait) -> bool:
        """处理 GeeTest 九宫格验证码（带重试机制）"""
        logger.info("开始处理 GeeTest 验证码...")
        
        try:
            # 获取验证码图片
            img_url = self.get_img(wait)
            if not img_url:
                logger.error("图片获取失败，刷新网页重试...")
                time.sleep(2)
                return False
            
            # 调用视觉模型识别
            recognition_result = self._recognize_captcha(img_url)
            if not recognition_result:
                logger.warning("识别失败，刷新网页重试...")
                time.sleep(2)
                return False
            
            logger.info(f"验证码识别结果: {recognition_result}")
            
            # 根据识别结果点击相应的九宫格
            if not self._click_captcha_items(driver, recognition_result):
                logger.warning("点击失败，刷新网页重试...")
                time.sleep(2)
                return False
            
            logger.warning("验证码流程完成，刷新网页验证是否成功...")
            time.sleep(2)
            return True
        except Exception as e:
            logger.error(f"处理验证码时发生错误: {e}", exc_info=True)
            return False

    
    def _recognize_captcha(self, img_url: str) -> Optional[Dict]:
        """使用视觉模型识别验证码"""
        try:
            prompt = (
    "任务：识别九宫格验证码中的物品。\n"
    "1. 从左到右、从上到下依次识别前9个格子中的物品名称。\n"
    "2. 最后识别左下角的参考图，其名称必须是前9个格子中出现过的名称（统一相似物品名称）。\n"
    "3. 输出一个纯 JSON 对象，键为 \"1\" 到 \"10\"，值为物品名称。\n"
    "4. 严格禁止输出任何其他文本、注释、代码块标记（如 ```json）、特殊标记（如 <|begin_of_box|>）、解释说明。\n"
    "5. 输出必须以 { 开头，以 } 结尾。\n"
    "示例正确输出：{\"1\":\"牛\",\"2\":\"牛\",\"3\":\"牛\",\"4\":\"牛\",\"5\":\"公交车\",\"6\":\"狗\",\"7\":\"钥匙\",\"8\":\"钥匙\",\"9\":\"轮胎\",\"10\":\"钥匙\"}"
)
            
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[{
                    'role': 'user',
                    'content': [
                        {'type': 'text', 'text': prompt},
                        {'type': 'image_url', 'image_url': {'url': img_url}}
                    ]
                }],
                stream=False
            )
            
            result_content = response.choices[0].message.content
            logger.info(f"模型原始输出: {result_content}")
            
            # 清理并解析 JSON
            cleaned_str = result_content.replace("'", '"')
            # 尝试提取 JSON 内容（处理可能包含其他文本的情况）
            json_match = json.loads(cleaned_str) if cleaned_str.startswith('{') else None
            
            result = extract_json_from_output(raw_output)
            if result is None:
                logger.error("无法从模型输出中提取有效 JSON")
                return None
                 
        except Exception as e:
            logger.error(f"验证码识别失败: {e}", exc_info=True)
            return None
    
    def _click_captcha_items(self, driver, recognition_result: Dict) -> bool:
        """
        根据识别结果点击九宫格中匹配的格子
        
        九宫格布局（索引从1开始）：
        1  2  3
        4  5  6
        7  8  9
        
        第10个是参考图（左下角）
        """
        try:
            # 获取参考图名称（第10个元素）
            target_name = recognition_result.get("10", "").strip()
            if not target_name:
                logger.error("未能从识别结果中获取参考图名称")
                return False
            
            logger.info(f"目标物品: {target_name}")
            
            # 获取所有九宫格元素（前9个）
            grid_items = driver.find_elements(By.CLASS_NAME, "geetest_item")
            
            # 排除最后一个（参考图），只处理前9个
            if len(grid_items) < 9:
                logger.error(f"九宫格元素数量不足，只找到 {len(grid_items)} 个")
                return False
            
            clickable_items = grid_items[:9]
            
            # 遍历前9个格子，找到匹配的物品并点击
            clicked_count = 0
            for i in range(9):
                position = i + 1  # 位置索引从1开始
                item_name = recognition_result.get(str(position), "").strip()
                
                logger.info(f"位置 {position}: {item_name}")
                
                # 如果当前格子的物品名称匹配参考图
                if item_name and item_name == target_name:
                    logger.info(f"找到匹配项！位置 {position} - {item_name}")
                    
                    # 点击该格子
                    try:
                        # 使用 JavaScript 点击，更稳定
                        driver.execute_script("arguments[0].click();", clickable_items[i])
                        clicked_count += 1
                        logger.info(f"已点击位置 {position}")
                        
                        # 点击后短暂等待，模拟人类操作
                        time.sleep(random.uniform(0.3, 0.6))
                        
                    except Exception as e:
                        logger.error(f"点击位置 {position} 时出错: {e}")
            
            if clicked_count == 0:
                logger.warning(f"未找到匹配 '{target_name}' 的格子")
                return False
            
            logger.info(f"共点击了 {clicked_count} 个匹配的格子")
            
            # 点击完成后，查找并点击确认按钮
            try:
                # 等待确认按钮变为可用状态（移除 geetest_disable 类）
                confirm_button = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "geetest_commit"))
                )
                
                # 检查按钮是否可用（没有 geetest_disable 类）
                button_classes = confirm_button.get_attribute("class")
                logger.info(f"确认按钮状态: {button_classes}")
                
                # 等待按钮变为可点击状态（最多等待3秒）
                max_wait = 3
                start = time.time()
                while "geetest_disable" in confirm_button.get_attribute("class"):
                    if time.time() - start > max_wait:
                        logger.warning("确认按钮未激活，但仍尝试点击")
                        break
                    time.sleep(0.2)
                    confirm_button = driver.find_element(By.CLASS_NAME, "geetest_commit")
                
                logger.info("找到确认按钮，准备点击...")
                driver.execute_script("arguments[0].click();", confirm_button)
                logger.info("已点击确认按钮")
                time.sleep(1)
            except TimeoutException:
                logger.info("未找到确认按钮，可能自动提交")
            
            return True
            
        except Exception as e:
            logger.error(f"点击验证码格子时发生错误: {e}", exc_info=True)
            return False
   
    def extract_json_from_output(raw_output: str) -> Optional[Dict]:
    """
    从模型原始输出中提取纯 JSON 对象。
    支持去除：
        - markdown 代码块标记（```json ... ```）
        - 特殊标记如 <|begin_of_box|>、<|end_of_box|>
        - 前后的任意空白、说明文字
    """
    # 1. 去除 markdown 代码块标记（不区分大小写）
    cleaned = re.sub(r'```json\s*|\s*```', '', raw_output, flags=re.IGNORECASE)
    
    # 2. 去除特殊标记（如 <|...|>）
    cleaned = re.sub(r'<\|.*?\|>', '', cleaned)
    
    # 3. 尝试直接解析整个字符串（如果已经是纯 JSON）
    try:
        return json.loads(cleaned.strip())
    except json.JSONDecodeError:
        pass
    
    # 4. 提取第一个 {...} 或 [...] 结构
    # 使用正则匹配最外层的 JSON 对象（支持嵌套）
    # 简单方式：找到第一个 '{' 和与之匹配的最后一个 '}'
    # 但更好的方式是使用栈匹配，这里用正则匹配最外层花括号（假设没有嵌套复杂字符串）
    # 为了稳健，使用正则匹配所有花括号内容，取最长的（但可能不准确）
    # 简单方案：找到第一个 '{' 和最后一个 '}'
    start = cleaned.find('{')
    if start == -1:
        return None
    end = cleaned.rfind('}')
    if end == -1:
        return None
    json_str = cleaned[start:end+1]
    
    # 尝试解析
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        # 如果仍然失败，可能是由于字符串中的单引号或其他问题
        # 尝试替换单引号为双引号（谨慎，因为值中可能包含单引号）
        # 这里采用简单替换，实际项目中可考虑 ast.literal_eval 或更安全的解析
        fixed_str = json_str.replace("'", '"')
        try:
            return json.loads(fixed_str)
        except json.JSONDecodeError:
            return None
    def _refresh_captcha(self, driver) -> bool:
        """刷新验证码"""
        try:
            logger.info("正在刷新验证码...")
            refresh_button = driver.find_element(By.CLASS_NAME, "geetest_refresh")
            driver.execute_script("arguments[0].click();", refresh_button)
            logger.info("已点击刷新按钮")
            time.sleep(1.5)  # 等待新验证码加载
            return True
        except Exception as e:
            logger.error(f"刷新验证码失败: {e}")
            return False
    
    def _wait_for_verification_result(self, driver, timeout: int = 10) -> str:
        """
        等待并检测验证结果（通过监听网络请求）
        
        返回值:
            "success": 验证成功
            "fail": 验证失败
            "closed": 验证码窗口已关闭
            "timeout": 超时
        """
        try:
            logger.info("监听验证结果...")
            start_time = time.time()
            
            # 清除之前的请求记录，只监听新的请求
            del driver.requests
            
            while time.time() - start_time < timeout:
                # 检查网络请求
                for request in driver.requests:
                    if request.response and 'api.geevisit.com/ajax.php' in request.url:
                        try:
                            # 获取响应内容
                            response_body = request.response.body.decode('utf-8')
                            logger.info(f"捕获到验证API响应: {response_body[:200]}")
                            
                            # 解析 JSONP 响应：geetest_xxx({"status": "success", ...})
                            json_match = re.search(r'geetest_\d+\((.*)\)', response_body)
                            if json_match:
                                json_str = json_match.group(1)
                                result_data = json.loads(json_str)
                                
                                status = result_data.get('status')
                                if status == 'success':
                                    data = result_data.get('data', {})
                                    result = data.get('result', '')
                                    
                                    if result == 'success':
                                        logger.info("✓ API返回验证成功")
                                        return "success"
                                    elif result == 'fail':
                                        logger.warning("✗ API返回验证失败")
                                        return "fail"
                            
                        except Exception as e:
                            logger.debug(f"解析响应时出错: {e}")
                
                # 同时检查验证码窗口是否关闭
                try:
                    widget = driver.find_element(By.CLASS_NAME, "geetest_widget")
                    if not widget.is_displayed():
                        logger.info("验证码窗口已关闭")
                        return "closed"
                except:
                    logger.info("验证码窗口未找到")
                    return "closed"
                
                time.sleep(0.5)
            
            logger.warning(f"验证结果等待超时 ({timeout}秒)")
            return "timeout"
            
        except Exception as e:
            logger.error(f"等待验证结果时出错: {e}", exc_info=True)
            return "timeout"
