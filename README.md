# web-ui

[![Software License](https://img.shields.io/badge/license-MIT-brightgreen.svg?style=flat-square)](LICENSE)

This repository is a web ui docker container for object detection and the other AI tasks. This micro-service is implemented by Flask. There are three tasks as separated.  
- COCO dataset([task01](http://ai.bakevision.com/task01))  
- Crested Gecko dataset([task02](http://ai.bakevision.com/task02))  
- Tsinghua-Tencent 100K dataset([task03](http://ai.bakevision.com/task03))  

## How to setup Object Detection Backend REST API Uri
You can edit the backend REST API for object detection.  

1. Edit /src/app.py file.  
2. Update below contants.   
```bash
POST_API_URI_TASK_01 = 'http://localhost:5001/detect_object?embed_image=false'  
POST_API_URI_TASK_02 = 'http://localhost:5002/detect_object?embed_image=false'  
POST_API_URI_TASK_03 = 'http://localhost:5003/detect_object?embed_image=false'  
```

## How to run  
The web ui docker container will be running via bash shell command. The default docker port is external(80) and internal(5000).  

```bash
./run.sh
```

## License and Citation

This project is made available under the [MIT License](https://github.com/asyncbridge/web-ui/blob/master/LICENSE).
