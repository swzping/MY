# 测试发票图片获取方式

你可以从以下几个地方方便获取发票图片用于测试：

## 方式一：百度图片搜索（最简单）
直接访问：https://image.baidu.com/search/index?tn=baiduimage&word=增值税电子普通发票

选择一张清晰的发票图片保存到本地即可测试。

## 方式二：国家税务总局官方样本
官网页面：http://www.chinatax.gov.cn/chinatax/n810341/n810755/c5141998/content_10000367.html

这里有官方发布的增值税电子发票样本。

## 方式三：使用手机拍照
直接拿你手边的一张真实发票拍照，传到电脑上测试更真实。

---

## 测试步骤

1. 启动本地服务器：
```bash
cd /Users/edy/Documents/agent-teams
python3 -m http.server 8080
```

2. 在浏览器打开：
```
http://localhost:8080/tools/invoice-assistant/index.html
```

3. 输入你的 OpenAI API Key

4. 选择刚才下载/拍照的发票图片上传

5. 点击"开始识别所有图片"

6. 查看识别结果是否准确

## 预期结果

AI 应该能正确识别出：
- 发票号码
- 开票日期（格式化为 YYYY-MM-DD）
- 总金额
- 税额
- 开票方名称

然后：
- 系统会自动检查发票号码是否重复
- 你确认无误后点击保存
- 最后可以导出 CSV 文件测试
