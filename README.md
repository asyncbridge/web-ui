# web-ui

[![Software License](https://img.shields.io/badge/license-MIT-brightgreen.svg?style=flat-square)](LICENSE)

This repository is a web ui docker container for object detection and the other AI tasks. This micro-service is implemented by Flask. There are three tasks as separated.  
- COCO dataset(task01)  
- Crested Gecko dataset(task02)  
- Tsinghua-Tencent 100K dataset(task03)  

# How to run  
The web ui docker container will be running via bash shell command. The default docker port is external(80) and internal(5000).  

```bash
./run.sh
```

## License and Citation

This project is made available under the [MIT License](https://github.com/asyncbridge/web-ui/blob/master/LICENSE).
