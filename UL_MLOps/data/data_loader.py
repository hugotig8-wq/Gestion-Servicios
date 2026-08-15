from torch.utils.data import DataLoader

from data.tokenizer import build_tokenizer
from data.dataset import UnlearningDataset
from data.split import split_dataset


def build_data_loaders(

    model_name: str,

    texts: list[str],

    batch_size: int = 8,

    max_length: int = 256,

    shuffle: bool = True,

):

    tokenizer = build_tokenizer(model_name)

    splits = split_dataset(texts)

    retain_dataset = UnlearningDataset(

        texts=splits["retain"],

        tokenizer=tokenizer,

        max_length=max_length

    )

    forget_dataset = UnlearningDataset(

        texts=splits["forget"],

        tokenizer=tokenizer,

        max_length=max_length

    )

    validation_dataset = UnlearningDataset(

        texts=splits["validation"],

        tokenizer=tokenizer,

        max_length=max_length

    )

    retain_loader = DataLoader(

        retain_dataset,

        batch_size=batch_size,

        shuffle=shuffle

    )

    forget_loader = DataLoader(

        forget_dataset,

        batch_size=batch_size,

        shuffle=shuffle

    )

    validation_loader = DataLoader(

        validation_dataset,

        batch_size=batch_size,

        shuffle=False

    )

    return (

        retain_loader,

        forget_loader,

        validation_loader

    )
