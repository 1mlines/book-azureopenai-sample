import { Example } from "./Example";

import styles from "./Example.module.css";

export type ExampleModel = {
    text: string;
    value: string;
};

const EXAMPLES: ExampleModel[] = [
    { text: "최충헌은 어떤 인물이었나요?", value: "최충헌은 어떤 인물이었나요?" },
    {
        text: "경대승은 기존의 최고 권력기구였던 중방을 무력화하고 새로운 권력 집단을 만들었습니다. 이 권력 집단의 이름은 무엇인가요?",
        value: "경대승은 기존의 최고 권력기구였던 중방을 무력화하고 새로운 권력 집단을 만들었습니다. 이 권력 집단의 이름은 무엇인가요?"
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
