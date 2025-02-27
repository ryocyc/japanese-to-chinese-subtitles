import streamlit as st
import whisper
from googletrans import Translator
import ffmpeg
import os

# 標題
st.title("日文語音轉中文字幕")

# 上傳影片檔案
uploaded_file = st.file_uploader("上傳影片檔案", type=["mp4", "avi", "mov"])

if uploaded_file is not None:
    # 保存上傳的影片
    video_path = "temp_video.mp4"
    with open(video_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # 從影片中提取音頻
    audio_path = "temp_audio.wav"
    try:
        (
            ffmpeg
            .input(video_path)
            .output(audio_path, ac=1, ar=16000)  # 設置音頻格式
            .run(capture_stdout=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:
        st.write(f"提取音頻失敗：{e.stderr.decode('utf-8')}")
        st.stop()

    # 使用 Whisper 進行語音轉文字
    st.write("正在轉換語音為文字...")
    model = whisper.load_model("base")  # 使用 base 模型（較快，但準確度較低）
    result = model.transcribe(audio_path)

    # 使用 Google 翻譯 API 進行翻譯
    translator = Translator()

    translated_segments = []
    for segment in result['segments']:
        # 確保文本是 UTF-8 編碼
        text = segment['text'].encode('utf-8', errors='ignore').decode('utf-8')
        
        # 翻譯日文到中文
        try:
            translated_text = translator.translate(text, src='ja', dest='zh-tw').text
            translated_segments.append({
                'start': segment['start'],
                'end': segment['end'],
                'text': translated_text
            })
        except Exception as e:
            st.write(f"翻譯失敗：{e}")
            # 如果翻譯失敗，保留原始日文文本
            translated_segments.append({
                'start': segment['start'],
                'end': segment['end'],
                'text': text
            })

    # 生成 SRT 檔案
    def generate_srt(segments):
        srt_content = ""
        for i, segment in enumerate(segments):
            start_time = format_time(segment['start'])
            end_time = format_time(segment['end'])
            text = segment['text']
            srt_content += f"{i + 1}\n{start_time} --> {end_time}\n{text}\n\n"
        return srt_content

    # 將秒數轉換為 SRT 時間格式
    def format_time(seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = seconds % 60
        return f"{hours:02}:{minutes:02}:{seconds:06.3f}".replace('.', ',')

    # 生成 SRT 內容
    srt_content = generate_srt(translated_segments)

    # 保存 SRT 檔案
    srt_path = "subtitles.srt"
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(srt_content)

    # 提供下載連結
    st.write("轉換完成！")
    with open(srt_path, "rb") as f:
        st.download_button("下載 SRT 檔案", f, file_name="subtitles.srt")

    # 清理臨時檔案
    os.remove(video_path)
    os.remove(audio_path)
    os.remove(srt_path)
