
import './ui_card.css';

const UICard = ({ children }: { children: React.ReactNode }) => {
    return (
        <div className="ui-card-container">
            {children}
        </div>
    );
};

export default UICard;