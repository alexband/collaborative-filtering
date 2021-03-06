# Know your customers

Project strucure:
* `src`: non-negative matrix factorization and denoising autoencoder implementation
* `autoencoder` fork of the [Hybrid Collaborative Filtering with Neural Networks](https://github.com/fstrub95/Autoencoders_cf) repository
* `input` where the data files should live
* `output` will include the predictions on the test dataset

## Matrix Factorization
To test whether the sequences are meaningful for the factorization,
it is possible to remove some ratings for each user by running:
```
python remove_ratings.py
```

### ALS-WR
To run the ALS-WR baseline, parse the ratings into a torch data file. 
The ratings file are supposed to having been placed in the `input` directory. 
```
th data.lua  -ratings input/customeraffinity.train -out input/customer-train.t7 -fileType alix -ratio 0.9
```
Then the actual ALS can be run by running the following command:
```
th ALS.lua -file <file> -lambda <lambda> -rank <rank> -seed <seed> 

e.g. th ALS.lua -file input/customer-train.t7 -rank 20 -lambda 0.1

-file         The relative path to your data file.
-lambda       Regularisation
-rank         Rank of the final matrix
-seed         The random seed
```


# Denoising autoencoder (requires tensorflow)

Parameters are shown using the `-h` option. To run training followed by prediction:
```
python AutoencoderRunner.py
```

# Hybrid Autoencoder for Collaborative filtering

### Running the network
Change the current working directory to `autoencoder/src`.

Run the network using a neural net configuration:
```
th main.lua  -file ../../input/customer-train.t7 -conf ../conf/conf.ratings.U.lua  -save ../output/network.R.t7 -type U -meta 0 -gpu 0
```
Compute metrics with the final network weights:
```
th computeMetrics.lua -file ../../input/customer-train.t7 -network ../output/network.R.t7 -type U -gpu 0
```

#### Install cutorch with GCC < 5
```
CC=gcc-4.8 CXX=g++4.8 luarocks install cutorch
```

#### Links
[Data exploration, SVD/ALS Baseline](http://www.grappa.univ-lille3.fr/~mary/cours/stats/centrale/reco/)
[Autoencoders for collaborative filtering](https://github.com/fstrub95/torch.github.io/blob/master/blog/_posts/2016-02-21-cfn.md)
