FROM python:3.8

RUN apt-get update && apt-get install -y \
      wget \
      xz-utils \
      bc \
      unzip
RUN apt-get install -y libgl1-mesa-dev \
      tesseract-ocr \
      libtesseract-dev

RUN wget -O /jpn.traineddata https://github.com/tesseract-ocr/tessdata/raw/main/jpn.traineddata
RUN wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz \
     && tar Jxvf ./ffmpeg-release-amd64-static.tar.xz

FROM python:3.8

RUN pip install --upgrade pip
COPY requirements.txt /tmp/
RUN pip install --upgrade pip
RUN pip install -r /tmp/requirements.txt

COPY --from=0 /go/src/github.com/alexellis/href-counter/app ./
COPY --from=0 /jpn.traineddata /usr/share/tesseract-ocr/4.00/tessdata/jpn.traineddata
COPY --from=0 /ROOT/ffmpeg-6.0-amd64-static/qt-faststart /usr/local/bin/
COPY --from=0 /ROOT/ffmpeg-6.0-amd64-static/ffmpeg /usr/local/bin/

WORKDIR /tmp

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

# ENTRYPOINT ["/root/bootstrap.sh"]
