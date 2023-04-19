FROM python:3.8

RUN pip install --upgrade pip
RUN pip install opencv-python
#RUN pip install tensorflow
RUN pip install tqdm
RUN pip install pillow
RUN pip install pyocr
RUN pip install pytesseract
RUN apt-get update && apt-get install -y \
      wget \
      xz-utils \
      bc \
      unzip
RUN apt-get install -y libgl1-mesa-dev \
      tesseract-ocr \
      libtesseract-dev

WORKDIR /tmp
RUN wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz \
     && tar Jxvf ./ffmpeg-release-amd64-static.tar.xz

RUN cp ./ffmpeg-6.0-amd64-static/qt-faststart /usr/local/bin/ \
      && cp ./ffmpeg-6.0-amd64-static/ffmpeg /usr/local/bin/
RUN pip install pandas

RUN wget -O /usr/share/tesseract-ocr/4.00/tessdata/jpn.traineddata https://github.com/tesseract-ocr/tessdata/raw/main/jpn.traineddata


# RUN wget -O /tmp/ffmpeg.zip https://www.osxexperts.net/ffmpeg6arm.zip
# RUN wget -O /tmp/ffmpeg.zip https://www.osxexperts.net/ffmpeg6intel.zip 
# RUN unzip /tmp/ffmpeg.zip -d /bin/

ADD ./model/ /root/model/
ADD ./apex-tracker.py /root/
ADD ./apex-create-movie.py /root/
ADD ./docker/bootstrap.sh /root/
ADD ./ocr/apex-ocr.py /root/
ADD ./ocr/apex-result.py /root/
ADD ./apex-kill-clip.sh /root/
ADD ./apex-ocr.sh /root/
ADD ./apex-ocr-exporter.sh /root/
ADD ./add_battle_result.sh /root/
# ADD ./ocr/jpn.traineddata /usr/share/tesseract-ocr/4.00/tessdata/
#ADD ./docker/ffmpeg /usr/local/bin/

ENTRYPOINT ["/root/bootstrap.sh"]
