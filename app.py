import streamlit as st
import yt_dlp
import os
import subprocess
import platform

st.markdown(
    """
    <style>
    .stApp {
        background-image: url("https://raw.githubusercontent.com/BKY1601/downly/main/res/img/bg.png");
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }
    </style>
    """,
    unsafe_allow_html=True
)
# Streamlit setup
st.set_page_config(page_title="Downly", page_icon="▶️")
st.title(<h1 style='text-align: center;'>"Downly"</h1> unsafe_allow_html=True)
st.caption("Download videos or extract MP3 audio from YouTube, instagram, and more — fast, easy, and hassle-free!")

# Detect OS and handle FFmpeg setup
if platform.system() == "Windows":
    FFMPEG_PATH = "ffmpeg" #if not detecting add winodws ffmeg folder path manually os.path.abspath
else:
    with st.spinner("Ensuring FFmpeg is installed..."):
        subprocess.run(["apt-get", "update"], check=False)
        subprocess.run(["apt-get", "install", "-y", "ffmpeg"], check=False)
    FFMPEG_PATH = "/usr/bin/ffmpeg"

# Initialize session state
if 'video_info' not in st.session_state:
    st.session_state.video_info = None
    st.session_state.selected_format = None

# Input for video URL
url = st.text_input("Enter Video URL")
continue_clicked = st.button(" ➜ ")

# Fetch video info
if url and continue_clicked:
    with st.spinner("Fetching video info..."):
        try:
            ydl_opts_info = {'quiet': True, 'skip_download': True}
            with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
                info_dict = ydl.extract_info(url, download=False)

            title = info_dict.get('title', 'Unknown Title')
            thumbnail = info_dict.get('thumbnail', '')
            formats = info_dict.get('formats', [])

            st.session_state.video_info = {
                'title': title,
                'thumbnail': thumbnail,
                'formats': formats
            }

            st.markdown(f"### {title}")
            if thumbnail:
                st.image(thumbnail, width=480)

        except Exception as e:
            st.error(f"Error fetching video info: {str(e)}")

# Format selection & download
if st.session_state.video_info:
    formats = st.session_state.video_info['formats']

    download_type = st.selectbox("Select Download Type", ["MP3 (Audio)", "MP4 (Best Video)", "Other (custom)"], index=0)

    selected_format_id = None
    file_ext = None

    if download_type == "Other (custom)":
        available_formats = [
            {
                'format_id': f['format_id'],
                'ext': f['ext'],
                'resolution': f.get('resolution') or f"{f.get('height', '?')}p",
                'filesize': f.get('filesize', 0),
            }
            for f in formats if f.get('vcodec') != 'none'
        ]

        selected = st.selectbox(
            "Choose a format",
            options=available_formats,
            format_func=lambda f: f"{f['resolution']} - .{f['ext']}"
        )

        selected_format_id = selected['format_id']
        file_ext = selected['ext']

    if st.button("Continue"):
        with st.spinner("Downloading..."):
            output_dir = "downloads"
            os.makedirs(output_dir, exist_ok=True)

            ydl_opts = {
                'ffmpeg_location': FFMPEG_PATH,
                'outtmpl': f'{output_dir}/%(title)s.%(ext)s',
                'noplaylist': True,
            }

            if download_type == "MP3 (Audio)":
                ydl_opts.update({
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                    'prefer_ffmpeg': True
                })
            elif download_type == "MP4 (Best Video)":
                ydl_opts.update({
                    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
                })
            elif download_type == "Other (custom)" and selected_format_id:
                ydl_opts.update({
                    'format': selected_format_id,
                })

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    result = ydl.extract_info(url, download=True)
                    filename = ydl.prepare_filename(result)
                    base_filename = os.path.basename(filename)

                st.write("Downloaded raw file:", filename)

                if download_type == "MP3 (Audio)":
                    mp3_filename = None
                    possible_exts = ('.webm', '.mp4', '.m4a', '.mkv')
                    for ext in possible_exts:
                        if filename.endswith(ext):
                            mp3_filename = filename.replace(ext, '.mp3')
                            break
                    if filename.endswith('.mp3'):
                        mp3_filename = filename

                    st.write("Expected MP3 filename:", mp3_filename)

                    if mp3_filename and os.path.exists(mp3_filename):
                        st.success("MP3 Download complete!")
                        with open(mp3_filename, "rb") as f:
                            st.download_button(
                                label="Click here to download the MP3 file",
                                data=f,
                                file_name=os.path.basename(mp3_filename),
                                mime="audio/mp3"
                            )
                        os.remove(mp3_filename)
                        if os.path.exists(filename):
                            os.remove(filename)
                    else:
                        st.error("MP3 file not found after conversion.")

                elif download_type == "MP4 (Best Video)":
                    if os.path.exists(filename):
                        st.success("MP4 Download complete!")
                        with open(filename, "rb") as f:
                            st.download_button(
                                label="Click here to download the MP4 file",
                                data=f,
                                file_name=base_filename,
                                mime="video/mp4"
                            )
                        os.remove(filename)
                    else:
                        st.error("MP4 file not found.")

                elif download_type == "Other (custom)":
                    if os.path.exists(filename):
                        st.success("Custom Format Download complete!")
                        ext = os.path.splitext(filename)[1].lower()
                        mime_type = "application/octet-stream"
                        if ext in [".mp4", ".mkv", ".webm"]:
                            mime_type = f"video/{ext[1:]}"
                        elif ext in [".mp3", ".m4a"]:
                            mime_type = f"audio/{ext[1:]}"
                        with open(filename, "rb") as f:
                            st.download_button(
                                label="Click here to download the file",
                                data=f,
                                file_name=base_filename,
                                mime=mime_type
                            )
                        os.remove(filename)
                    else:
                        st.error("File not found for custom format.")

            except Exception as e:
                st.error(f"Download failed: {str(e)}")
