import { Button, Result, Typography } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';

const { Paragraph, Text } = Typography;

interface ErrorInfo {
  status: '403' | '404' | '500' | 'error';
  title: string;
  subTitle: string;
  details?: string;
}

const errorMessages: Record<string, ErrorInfo> = {
  '403': {
    status: '403',
    title: '403',
    subTitle: '접근 권한이 없습니다.',
    details: '이 페이지에 접근할 권한이 없습니다. 관리자에게 문의하세요.',
  },
  '404': {
    status: '404',
    title: '404',
    subTitle: '페이지를 찾을 수 없습니다.',
    details: '요청하신 페이지가 존재하지 않거나 이동되었습니다.',
  },
  '500': {
    status: '500',
    title: '500',
    subTitle: '서버 오류가 발생했습니다.',
    details: '서버에서 요청을 처리하는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.',
  },
  'network': {
    status: 'error',
    title: '네트워크 오류',
    subTitle: '서버에 연결할 수 없습니다.',
    details: 'API 서버(http://localhost:8000)가 실행 중인지 확인해주세요.',
  },
  'unknown': {
    status: 'error',
    title: '오류 발생',
    subTitle: '알 수 없는 오류가 발생했습니다.',
    details: '문제가 지속되면 관리자에게 문의하세요.',
  },
};

interface ErrorPageProps {
  errorCode?: string;
  errorMessage?: string;
  errorStack?: string;
}

export function ErrorPage({ errorCode, errorMessage, errorStack }: ErrorPageProps) {
  const navigate = useNavigate();
  const location = useLocation();

  // Get error info from URL state or props
  const state = location.state as { errorCode?: string; errorMessage?: string; errorStack?: string } | null;
  const code = errorCode || state?.errorCode || 'unknown';
  const message = errorMessage || state?.errorMessage;
  const stack = errorStack || state?.errorStack;

  const errorInfo = errorMessages[code] || errorMessages['unknown'];

  return (
    <Result
      status={errorInfo.status}
      title={errorInfo.title}
      subTitle={errorInfo.subTitle}
      extra={[
        <Button type="primary" key="home" onClick={() => navigate('/')}>
          대시보드로 돌아가기
        </Button>,
        <Button key="back" onClick={() => navigate(-1)}>
          이전 페이지
        </Button>,
        <Button key="reload" onClick={() => window.location.reload()}>
          새로고침
        </Button>,
      ]}
    >
      <div style={{ textAlign: 'left', maxWidth: 600, margin: '0 auto' }}>
        <Paragraph>
          <Text strong>원인:</Text> {errorInfo.details}
        </Paragraph>

        {message && (
          <Paragraph>
            <Text strong>에러 메시지:</Text>
            <pre style={{
              background: '#f5f5f5',
              padding: 12,
              borderRadius: 4,
              overflow: 'auto',
              maxHeight: 100,
              fontSize: 12,
            }}>
              {message}
            </pre>
          </Paragraph>
        )}

        {stack && process.env.NODE_ENV === 'development' && (
          <Paragraph>
            <Text strong>스택 트레이스 (개발 모드):</Text>
            <pre style={{
              background: '#fff2f0',
              padding: 12,
              borderRadius: 4,
              overflow: 'auto',
              maxHeight: 200,
              fontSize: 11,
              color: '#cf1322',
            }}>
              {stack}
            </pre>
          </Paragraph>
        )}
      </div>
    </Result>
  );
}
