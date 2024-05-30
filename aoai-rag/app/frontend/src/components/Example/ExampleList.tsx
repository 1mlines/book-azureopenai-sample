import { Example } from "./Example";

import styles from "./Example.module.css";

export type ExampleModel = {
    text: string;
    value: string;
};

const EXAMPLES: ExampleModel[] = [
    { text: "최충헌에 대해서 알려줘.", value: "최충헌에 대해서 알려줘." },
    {
        text: "최우가 기여한 경전의 이름과 특징은?",
        value: "최우가 기여한 경전의 이름과 특징은?"
    },
    {
        text: "경대승은 어떤 인물이야?",
        value: "경대승은 어떤 인물이야?"
    }
];

interface Props {
    onExampleClicked: (value: string) => void;
}

export const ExampleList = ({ onExampleClicked }: Props) => {
    return (
        <ul className={styles.examplesNavList}>
            {EXAMPLES.map((x, i) => (
                <li key={i}>
                    <Example text={x.text} value={x.value} onClick={onExampleClicked} />
                </li>
            ))}
        </ul>
    );
};
