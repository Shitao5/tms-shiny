import json
import base64
import shiny

SecretId = "YOUR_SecretId"
SecretKey = "YOUR_SecretKey"

from tencentcloud.common.common_client import CommonClient
from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile

def init_client():
    cred = credential.Credential(SecretId, SecretKey)
    httpProfile = HttpProfile()
    httpProfile.endpoint = "tms.tencentcloudapi.com"
    clientProfile = ClientProfile()
    clientProfile.httpProfile = httpProfile
    return CommonClient("tms", "2020-12-29", cred, "ap-shanghai", profile=clientProfile)

def server(input, output, session):
    client = init_client()
    last_click = [0]  # Initialize last click with 0

    @output(id="result")
    @shiny.render.text
    def result():
        current_click = input.analyze_btn()  # Get the current click count
        if current_click == last_click[0]:  # Check if there has been a new click
            return ""  # Return empty string if no new click

        last_click[0] = current_click  # Update the last click count

        content = input.text_input()
        if not content:
            return "<p>请输入文本后点击「分析」按钮进行文本内容检查。</p>"
        
        try:
            encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
            params = f'{{"Content":"{encoded_content}"}}'
            response = client.call_json("TextModeration", json.loads(params))
            return format_result(response, content)
        except TencentCloudSDKException as err:
            return f"<p>错误: {str(err)}</p>"

def format_result(response, original_text):
    response_data = response.get("Response")
    if response_data and response_data.get("Keywords"):
        keywords = response_data.get("Keywords")
        for keyword in keywords:
            highlighted = f"<span style='background-color: yellow;'>{keyword}</span>"
            original_text = original_text.replace(keyword, highlighted)
    return f"<p style='white-space: pre-wrap;'>{original_text}</p>"  # 使用 pre-wrap 保持原始格式

app_ui = shiny.ui.page_fluid(
    shiny.ui.layout_sidebar(
        shiny.ui.panel_sidebar(
            shiny.ui.input_text_area("text_input", "请输入待检查文本：", rows=3, autoresize=True),
            shiny.ui.input_action_button("analyze_btn", "分析")
        ),
        shiny.ui.panel_main(
            shiny.ui.output_ui("result")
        )
    )
)

app = shiny.App(ui=app_ui, server=server)

if __name__ == "__main__":
    shiny.run_app(app)