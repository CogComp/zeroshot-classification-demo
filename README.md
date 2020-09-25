# zeroshotdemo

New Step 1: copy all pretrained entailment models from /shared folder.

$ cp -r /shared/jinruiy/0shot/BenchmarkingZeroShot/models/demo_models  <the path of FOLDER you wanna save pretrained models>

Step 2: Download ESA word2id.json and matrix from the URL https://drive.google.com/file/d/18I-cSzhEoKgfCEfpnWKq2yEhES7_roaS/view?usp=sharing

Step 3 : 

$ CUDA_VISIBLE_DEVICES=2,3 python3 backend_cherry.py --ZEROSHOT_MODELS <the path of FOLDER you save pretrained model from step 1> --ZEROSHOT_RESOURCES <the path of FOLDER you save ESA from step 2>  

Note: Please keep eye on just the folder path, not the files path. 

New Step 4:
then in another termianl tab enter, you can Check backend with terminal:

curl -d '{"text":"The fox jumped over the fence, and the fence fell down.","models":["Bert-MNLI","Bert-FEVER", "Bert-RTE", "ESA", "Bart-MNLI","Bart-FEVER", "Bart-RTE"],"labels":["Society", "Health", "Sports"], "descriptions":["society des"]}' -H 'Content-Type: application/json' -X POST http://dickens.seas.upenn.edu:4007/predict

Step 5:
 
Open url http://dickens.seas.upenn.edu:4007/ in the browser, then you can play with it!
