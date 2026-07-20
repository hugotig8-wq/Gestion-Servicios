from torch.utils.data import Dataset
import hashlib


class UnlearningDataset(Dataset):

    def __init__(

        self,

        texts: list[str],

        tokenizer,

        max_length: int = 256

    ):

        self.texts = texts

        self.tokenizer = tokenizer

        self.max_length = max_length

        self.ids = [

            hashlib.sha256(

                text.encode("utf-8")

            ).hexdigest()

            for text in texts

        ]

    def __len__(self):

        return len(self.texts)

    def __getitem__(

        self,

        index

    ):

        text = self.texts[index]

        example_id = self.ids[index]

        encoding = self.tokenizer(

            text,

            truncation=True,

            padding="max_length",

            max_length=self.max_length,

            return_tensors="pt"

        )

        input_ids = encoding["input_ids"].squeeze(0)

        attention_mask = encoding["attention_mask"].squeeze(0)

        labels = input_ids.clone()

        labels[attention_mask == 0] = -100

        return {

            "id": example_id,

            "input_ids": input_ids,

            "attention_mask": attention_mask,

            "labels": labels

        }
