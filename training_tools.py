import pickle
import os
import torch
from torch.distributed import (
    all_reduce,
    ReduceOp,
)

class loss_track:
    def __init__(self, project="time_series_pred"):
        self.project = project
        self.temp_loss = 0
        self.counter = 1

    def update(self, loss):
        self.temp_loss += loss
        self.counter += 1

    def reset(self):
        self.temp_loss = 0
        self.counter = 1

    def get_loss(self):
        if self.counter == 0:
            return self.temp_loss
        return self.temp_loss / self.counter

    def all_reduce(self, gpu_id):
        
        loss_tensor = torch.tensor(
            [self.temp_loss, self.counter], device=gpu_id, dtype=torch.float32
            )
        all_reduce(loss_tensor, ReduceOp.SUM, async_op=True)
        self.temp_loss, self.counter = loss_tensor.tolist()
    
    @property
    def loss(self)->float:
        return self.temp_loss / self.counter

class loss_track_MA:
    """
    This dudes keeps track of the history of the loss in a rolling mean sense!!!
    """
    def __init__(self, project="time_series_pred", 
                 file_name: str = "loss.log", 
                 file_dir: str = "loss_log",
                 initial_val_for_loss = 1e-10,
                 ) -> None:
        ## File name for logging loss logs ##
        self.file_name = file_name
        self.project_name = project
        ## --------------- ##
        ## We do not just keep track the mean loss
        ## but also standard deviation along the batches
        self._loss = initial_val_for_loss
        ## history »»
        self._loss_hist = [self._loss]
        ## counters for rolling mean and variance ##
        self.counter = 1
        ### epochs
        self.num_epochs = 0

        self.local_path = os.path.join(file_dir, file_name)
        if not os.path.isfile(self.local_path):
            try:
                os.mkdir(file_dir)
            except Exception as e:
                print(f"Something went wrong with: {e}")

    def update(self, loss: float) -> None:
        ## update mean loss and variance loss ##
        self._loss -= (self._loss - loss) / (self.counter + 1)
        ## append the real losses for future analysis
        self._loss_hist.append(self._loss)
        ## update the counter
        self.counter += 1

    def reset(self) -> None:
        ### update the number of epochs passed
        self.num_epochs += 1
        self.counter = 1
        self.__flush__()
    
    def all_reduce(self):
        if torch.cuda.is_available():
            device = torch.device("cuda")
            loss_tensor = torch.tensor(
            [self.temp_loss, self.counter], device=device, dtype=torch.float32
            )
            all_reduce(loss_tensor, ReduceOp.AVG, async_op=True)
            self.temp_loss, self.counter = loss_tensor.tolist()
    


    def __flush__(self) -> None:
        dict_ = {
            "project_name": self.project_name,
            "Epoch": self.num_epochs,
            "Loss": self._loss,
            "Loss History": self._loss_hist,
        }
        with open(self.local_path+f"epoch_{self.num_epochs}", mode="ab") as file:
            pickle.dump(dict_, file)

    @property
    def loss(self)->float:
        return self._lost
"""
a = loss_track_MA()

a.update(1234.23)

a.reset()
"""
if __name__ == "__main__":
    print("OK Boomer!!!")
