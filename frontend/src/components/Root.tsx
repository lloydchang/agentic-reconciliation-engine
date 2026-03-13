import React from 'react';

interface RootProps {
  children: React.ReactNode;
}

const Root: React.FC<RootProps> = ({ children }) => (
  <div>
    {children}
  </div>
);

export default Root;
