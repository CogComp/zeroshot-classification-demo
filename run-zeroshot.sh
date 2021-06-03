export CUDA_VISIBLE_DEVICES=2,3
while [ 1 -eq 1 ]
do
	python3 backend_cherry.py --ZEROSHOT_MODELS /shared/ccgadmin/demos/ZeroShotDemo/BenchmarkingZeroShotData  --ZEROSHOT_RESOURCES /shared/ccgadmin/demos/ZeroShotDemo
done

