import torch
from torch import nn as nn
from torch.nn import functional as F
from layers import block, Upsampling, Linear




class Model(nn.Module):
    def __init__(
        self,
        lags: int = 512,
        embedding_dim: int = 64,
        n_blocks: int = 10,
        pool_size: int = 4,
        number_of_heads=4,
        number_ts=25,
        num_of_clusters=None,  ### number of clusters of times series
        channel_shuffle_group=2,  ## active only and only when channel_shuffle is True
    ):
        assert (
            lags / pool_size
        ).is_integer(), "Lag size should be divisible by pool_size"
        super().__init__()
        self.width = lags // pool_size
        self.embedding_dim = embedding_dim
        ###
        self.cluster_used = True if num_of_clusters is not None else False
        ###
        self.blocks = nn.Sequential(
            *(
                block(
                    embedding_dim,
                    width=self.width,
                    n_heads=number_of_heads,
                )
                for _ in range(n_blocks)
            )
        )
        self.up_sampling = Upsampling(
            lags=lags,
            d_out=self.embedding_dim,
            pool_size=pool_size,
            num_of_ts=number_ts,
            conv_activation=F.gelu,
            num_of_clusters=num_of_clusters,
            channel_shuffle_group=channel_shuffle_group,
        )

        ###
        self.Linear = Linear(self.embedding_dim, 1)
        ###

    @classmethod 
    def from_config_file(cls, config_file):
        pass
    @classmethod
    def from_pretrained(cls, file_name, config_file):
        pass
    @classmethod
    def from_data_class(cls, data_class):
        pass
    def write_config_file(self, file_name):
        pass
    
    def save_model(self, file_name = None):
        fn = "Model" if file_name == None else file_name
        try:
            torch.save(self.state_dict(), f"{fn}")
            print("Model saved succesfully")
        except Exception as exp:
            print(f"{exp}")
        
        
    def forward(self, x):
        ## Here we go with upsampling layer
        if self.cluster_used:
            x, tse_embedding, cluster_embedding = x[0], x[1], x[2]
            x = self.up_sampling((x, tse_embedding, cluster_embedding))
        else:
            x, tse_embedding = x[0], x[1]
            x = self.up_sampling((x, tse_embedding))
        ## Concatted transformer blocks
        ###
        x = self.blocks(x)
        return self.Linear(x)
    