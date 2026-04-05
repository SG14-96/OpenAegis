declare global {
    type User = {
        user_uuid: string;
        username: string;
        email: string;
        full_name: string;
        last_name: string;
        is_superuser: boolean;
    };
}

export { };
