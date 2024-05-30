import { Example } from "./Example";

import styles from "./Example.module.css";

export type ExampleModel = {
    text: string;
    value: string;
};

const EXAMPLES: ExampleModel[] = [
    { text: "두경승은 어떤 인물이야?", value: "두경승은 어떤 인물이야?" },
    {
        text: "최우가 기여한 경전의 이름과 특징은?",
        value: "최우가 기여한 경전의 이름과 특징은?"
    },
    {
        text: "정중부, 이고와 함께 무신정변을 일으킨 인물의 이름과 이 인물의 출신지에 있는 카페의 이름을 알려줘.",
        value: "정중부, 이고와 함께 무신정변을 일으킨 인물의 이름과 이 인물의 출신지에 있는 카페의 이름을 알려줘."
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
