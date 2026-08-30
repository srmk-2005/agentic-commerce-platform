import React, { useEffect, useState } from 'react';
import { Campaign, CampaignStatus, Merchant } from '../types';
import { campaignService } from '../services/campaignService';
import { Megaphone, Play, Pause, RefreshCw } from 'lucide-react';

interface CampaignsPageProps {
  currentMerchant: Merchant | null;
}

export const CampaignsPage: React.FC<CampaignsPageProps> = ({ currentMerchant }) => {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<CampaignStatus | 'ALL'>('ALL');

  const fetchCampaigns = async () => {
    if (!currentMerchant) return;
    try {
      setLoading(true);
      const data = await campaignService.getCampaigns({
        merchant_id: currentMerchant.id,
        status: statusFilter === 'ALL' ? undefined : statusFilter,
      });
      setCampaigns(data);
    } catch (err) {
      console.error('Failed to load campaigns:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCampaigns();
  }, [currentMerchant, statusFilter]);

  const handleTogglePause = async (campaign: Campaign) => {
    try {
      if (campaign.status === 'ACTIVE') {
        await campaignService.pauseCampaign(campaign.id);
      } else {
        await campaignService.activateCampaign(campaign.id);
      }
      fetchCampaigns();
    } catch (err) {
      console.error('Failed to toggle campaign status:', err);
    }
  };

  const getStatusBadge = (status: CampaignStatus) => {
    switch (status) {
      case 'ACTIVE':
        return { bg: 'rgba(16, 185, 129, 0.15)', color: '#34d399', border: 'rgba(16, 185, 129, 0.3)', label: 'Active' };
      case 'PAUSED':
        return { bg: 'rgba(245, 158, 11, 0.15)', color: '#fbbf24', border: 'rgba(245, 158, 11, 0.3)', label: 'Paused' };
      case 'DRAFT':
        return { bg: 'rgba(148, 163, 184, 0.15)', color: '#cbd5e1', border: 'rgba(148, 163, 184, 0.3)', label: 'Draft' };
      case 'REJECTED':
        return { bg: 'rgba(239, 68, 68, 0.15)', color: '#fca5a5', border: 'rgba(239, 68, 68, 0.3)', label: 'Rejected' };
      default:
        return { bg: 'rgba(99, 102, 241, 0.15)', color: '#a5b4fc', border: 'rgba(99, 102, 241, 0.3)', label: status };
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header */}
      <div
        className="glass-card"
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '16px',
          padding: '20px 24px',
          background: 'linear-gradient(135deg, rgba(56, 189, 248, 0.08) 0%, rgba(99, 102, 241, 0.08) 100%)',
          borderColor: 'rgba(56, 189, 248, 0.25)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div
            style={{
              width: '46px',
              height: '46px',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, #0284C7 0%, #6366F1 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Megaphone size={24} color="white" />
          </div>
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-main)' }}>
              Campaigns & Active Promotions
            </h2>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '2px' }}>
              Merchant-approved cross-sells, product bundles, and inventory promotions.
            </p>
          </div>
        </div>

        <button
          type="button"
          className="btn btn-secondary btn-sm"
          onClick={fetchCampaigns}
          disabled={loading}
          style={{ gap: '6px' }}
        >
          <RefreshCw size={14} className={loading ? 'spinning' : ''} /> Refresh
        </button>
      </div>

      {/* Filter Tabs */}
      <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '8px' }}>
        {[
          { label: 'All Campaigns', value: 'ALL' },
          { label: 'Active', value: 'ACTIVE' },
          { label: 'Paused', value: 'PAUSED' },
          { label: 'Draft', value: 'DRAFT' },
        ].map((tab) => (
          <button
            key={tab.value}
            type="button"
            className={`btn btn-sm ${statusFilter === tab.value ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setStatusFilter(tab.value as any)}
            style={{ borderRadius: '8px' }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Campaigns Table */}
      <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Campaign</th>
                <th>Type</th>
                <th>Target Products</th>
                <th>Status</th>
                <th>Created By</th>
                <th>Dates</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '32px' }}>
                    <RefreshCw size={20} className="spinning" style={{ margin: '0 auto 8px' }} />
                    Loading campaigns...
                  </td>
                </tr>
              ) : campaigns.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '36px', color: 'var(--text-dim)' }}>
                    No campaigns found in this view.
                  </td>
                </tr>
              ) : (
                campaigns.map((camp) => {
                  const badge = getStatusBadge(camp.status);
                  return (
                    <tr key={camp.id}>
                      <td>
                        <div style={{ fontWeight: 600, color: 'var(--text-main)' }}>{camp.name}</div>
                        {camp.description && (
                          <div style={{ fontSize: '0.775rem', color: 'var(--text-dim)', marginTop: '2px', maxWidth: '300px' }}>
                            {camp.description}
                          </div>
                        )}
                      </td>

                      <td>
                        <span
                          style={{
                            fontSize: '0.7rem',
                            fontWeight: 700,
                            padding: '2px 8px',
                            borderRadius: '4px',
                            background: 'rgba(99, 102, 241, 0.12)',
                            color: '#a5b4fc',
                            border: '1px solid rgba(99, 102, 241, 0.25)',
                          }}
                        >
                          {camp.campaign_type.replace(/_/g, ' ')}
                        </span>
                      </td>

                      <td>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                          {camp.products.map((cp) => (
                            <span
                              key={cp.id}
                              style={{
                                fontSize: '0.725rem',
                                padding: '2px 6px',
                                borderRadius: '4px',
                                background: 'rgba(255, 255, 255, 0.05)',
                                color: 'var(--text-main)',
                              }}
                            >
                              {cp.product_name || `Product #${cp.product_id}`}
                            </span>
                          ))}
                        </div>
                      </td>

                      <td>
                        <span
                          style={{
                            fontSize: '0.75rem',
                            fontWeight: 700,
                            padding: '3px 8px',
                            borderRadius: '6px',
                            background: badge.bg,
                            color: badge.color,
                            border: `1px solid ${badge.border}`,
                          }}
                        >
                          {badge.label}
                        </span>
                      </td>

                      <td style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>
                        {camp.created_by}
                      </td>

                      <td style={{ fontSize: '0.775rem', color: 'var(--text-dim)' }}>
                        {camp.start_date ? new Date(camp.start_date).toLocaleDateString() : 'Immediate'}
                        {camp.end_date ? ` → ${new Date(camp.end_date).toLocaleDateString()}` : ''}
                      </td>

                      <td>
                        {camp.status === 'ACTIVE' && (
                          <button
                            type="button"
                            className="btn btn-secondary btn-sm"
                            onClick={() => handleTogglePause(camp)}
                            style={{ gap: '4px', fontSize: '0.75rem' }}
                          >
                            <Pause size={12} /> Pause
                          </button>
                        )}
                        {camp.status === 'PAUSED' && (
                          <button
                            type="button"
                            className="btn btn-primary btn-sm"
                            onClick={() => handleTogglePause(camp)}
                            style={{ gap: '4px', fontSize: '0.75rem' }}
                          >
                            <Play size={12} /> Resume
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
