import { Result, Button } from 'antd';
import { useNavigate } from 'react-router-dom';

interface PlaceholderPageProps {
  title: string;
  subtitle?: string;
}

export function PlaceholderPage({ title, subtitle }: PlaceholderPageProps) {
  const navigate = useNavigate();

  return (
    <Result
      status="info"
      title={title}
      subTitle={subtitle || '이 페이지는 현재 개발 중입니다.'}
      extra={
        <Button type="primary" onClick={() => navigate('/')}>
          대시보드로 돌아가기
        </Button>
      }
    />
  );
}
