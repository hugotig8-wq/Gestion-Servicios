from sklearn.model_selection import train_test_split


def split_dataset(

    texts: list[str],

    forget_ratio: float = 0.10,

    validation_ratio: float = 0.10,

    random_state: int = 42

):

    retain_texts, forget_texts = train_test_split(

        texts,

        test_size=forget_ratio,

        random_state=random_state,

        shuffle=True

    )

    retain_texts, validation_texts = train_test_split(

        retain_texts,

        test_size=validation_ratio,

        random_state=random_state,

        shuffle=True

    )

    return {

        "retain": retain_texts,

        "forget": forget_texts,

        "validation": validation_texts

    }
